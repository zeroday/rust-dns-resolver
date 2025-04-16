use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use clap::Parser;
use futures::{stream::FuturesUnordered, StreamExt};
use rusqlite::{params, Connection};
use serde::Deserialize;
use std::{
    collections::HashSet,
    net::IpAddr,
    sync::Arc,
    time::{Duration, Instant},
};
use tokio::time::timeout;
use trust_dns_resolver::{
    config::{ResolverConfig, ResolverOpts},
    TokioAsyncResolver,
};
use rand::seq::SliceRandom;
use rand::thread_rng;
use reqwest::Client;
use serde_json::Value;

#[derive(Deserialize)]
struct IpApiResponse {
    #[serde(rename = "as")]
    asn: String,
    #[serde(rename = "asname")]
    as_name: String,
}

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to the input file containing hostnames
    #[arg(short, long)]
    input: Option<String>,

    /// Path to the SQLite database file
    #[arg(short, long, default_value = "dns_results.db")]
    database: String,

    /// Timeout in seconds for DNS resolution
    #[arg(short, long, default_value_t = 5)]
    timeout: u64,

    /// Number of concurrent DNS lookups
    #[arg(short, long, default_value_t = 10)]
    concurrency: usize,

    /// Pattern to generate hostnames (e.g., "a{2}.com" for aa.com, ab.com, etc.)
    #[arg(short, long)]
    pattern: Option<String>,

    /// Shuffle the order of hostnames before processing
    #[arg(short, long, default_value_t = false)]
    shuffle: bool,

    /// Number of concurrent HTTP requests
    #[arg(short, long, default_value_t = 100)]
    http_concurrency: usize,
}

#[derive(Debug, Clone)]
struct DnsResult {
    hostname: String,
    ip_address: Option<String>,
    asn: Option<String>,
    as_name: Option<String>,
    timestamp: DateTime<Utc>,
    success: bool,
    error: Option<String>,
}

#[derive(Debug)]
struct HttpResult {
    hostname: String,
    path: String,
    status_code: u16,
    response: Option<String>,
    timestamp: DateTime<Utc>,
    error: Option<String>,
}

fn generate_hostnames_from_pattern(pattern: &str) -> Vec<String> {
    let mut hostnames = Vec::new();
    let mut current_pattern = pattern.to_string();
    
    // Find all [a-z]{n} patterns
    while let Some(start) = current_pattern.find("[a-z]{") {
        if let Some(end) = current_pattern[start..].find('}') {
            let end = start + end + 1;
            let length_str = &current_pattern[start + 6..end - 1];
            if let Ok(length) = length_str.parse::<usize>() {
                let prefix = &current_pattern[..start];
                let suffix = &current_pattern[end..];
                
                // Generate all combinations
                let mut combinations = Vec::new();
                generate_combinations("", length, &mut combinations);
                
                // Replace the pattern with each combination
                for combo in combinations {
                    let hostname = format!("{}{}{}", prefix, combo, suffix);
                    hostnames.push(hostname);
                }
                
                // We only handle one pattern at a time for simplicity
                break;
            }
        }
    }
    
    hostnames
}

fn generate_combinations(prefix: &str, length: usize, combinations: &mut Vec<String>) {
    if prefix.len() == length {
        combinations.push(prefix.to_string());
        return;
    }
    
    for c in b'a'..=b'z' {
        let new_prefix = format!("{}{}", prefix, c as char);
        generate_combinations(&new_prefix, length, combinations);
    }
}

async fn lookup_asn(ip: &str) -> Option<(String, String)> {
    let url = format!("http://ip-api.com/json/{}?fields=as,asname", ip);
    match reqwest::get(&url).await {
        Ok(response) => {
            match response.json::<IpApiResponse>().await {
                Ok(data) => Some((data.asn, data.as_name)),
                Err(_) => None,
            }
        }
        Err(_) => None,
    }
}

async fn resolve_hostname(
    hostname: String,
    resolver: &TokioAsyncResolver,
    timeout_duration: Duration,
) -> DnsResult {
    let timestamp = Utc::now();

    match timeout(timeout_duration, resolver.lookup_ip(&hostname)).await {
        Ok(Ok(lookup)) => {
            let ips: Vec<String> = lookup.iter().map(|ip| ip.to_string()).collect();
            let ip = ips.first().cloned();
            
            // Get ASN info for the first IP address
            let asn_info = if let Some(ip) = &ip {
                lookup_asn(ip).await
            } else {
                None
            };

            DnsResult {
                hostname,
                ip_address: ip,
                asn: asn_info.as_ref().map(|(asn, _)| asn.clone()),
                as_name: asn_info.as_ref().map(|(_, name)| name.clone()),
                timestamp,
                success: true,
                error: None,
            }
        }
        Ok(Err(e)) => DnsResult {
            hostname,
            ip_address: None,
            asn: None,
            as_name: None,
            timestamp,
            success: false,
            error: Some(e.to_string()),
        },
        Err(_) => DnsResult {
            hostname,
            ip_address: None,
            asn: None,
            as_name: None,
            timestamp,
            success: false,
            error: Some("Timeout".to_string()),
        },
    }
}

async fn check_http_endpoint(
    client: &Client,
    hostname: &str,
    path: &str,
    timeout_duration: Duration,
) -> HttpResult {
    let url = format!("https://{}{}", hostname, path);
    let timestamp = Utc::now();

    match timeout(timeout_duration, client.get(&url).send()).await {
        Ok(Ok(response)) => {
            let status_code = response.status().as_u16();
            let response_text = if status_code == 200 {
                match response.text().await {
                    Ok(text) => Some(text),
                    Err(e) => Some(format!("Error reading response: {}", e)),
                }
            } else {
                None
            };

            HttpResult {
                hostname: hostname.to_string(),
                path: path.to_string(),
                status_code,
                response: response_text,
                timestamp,
                error: None,
            }
        }
        Ok(Err(e)) => HttpResult {
            hostname: hostname.to_string(),
            path: path.to_string(),
            status_code: 0,
            response: None,
            timestamp,
            error: Some(e.to_string()),
        },
        Err(_) => HttpResult {
            hostname: hostname.to_string(),
            path: path.to_string(),
            status_code: 0,
            response: None,
            timestamp,
            error: Some("Timeout".to_string()),
        },
    }
}

fn init_database(conn: &Connection) -> Result<()> {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS dns_results (
            id INTEGER PRIMARY KEY,
            hostname TEXT NOT NULL,
            ip_address TEXT,
            asn TEXT,
            as_name TEXT,
            timestamp TEXT NOT NULL,
            success INTEGER NOT NULL,
            error TEXT
        )",
        [],
    )?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY,
            hostname TEXT NOT NULL,
            status_code INTEGER,
            path TEXT,
            timestamp TEXT NOT NULL,
            response TEXT
        )",
        [],
    )?;

    Ok(())
}

fn save_result(conn: &Connection, result: &DnsResult) -> Result<()> {
    conn.execute(
        "INSERT INTO dns_results (hostname, ip_address, asn, as_name, timestamp, success, error)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        params![
            result.hostname,
            result.ip_address,
            result.asn,
            result.as_name,
            result.timestamp.to_rfc3339(),
            result.success,
            result.error,
        ],
    )?;
    Ok(())
}

fn save_http_result(conn: &Connection, result: &HttpResult) -> Result<()> {
    conn.execute(
        "INSERT INTO status (hostname, status_code, path, timestamp, response)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![
            result.hostname,
            result.status_code,
            result.path,
            result.timestamp.to_rfc3339(),
            result.response,
        ],
    )?;
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing for logging
    tracing_subscriber::fmt::init();

    println!("Starting DNS resolver...");
    
    // Parse command line arguments
    let args = Args::parse();
    println!("Arguments parsed: {:?}", args);
    
    let timeout_duration = Duration::from_secs(args.timeout);

    // Generate hostnames from pattern if provided
    let mut hostnames = if let Some(pattern) = args.pattern {
        println!("Generating hostnames from pattern: {}", pattern);
        let generated = generate_hostnames_from_pattern(&pattern);
        println!("Generated {} hostnames", generated.len());
        generated
    } else {
        Vec::new()
    };

    // Add hostnames from input file if provided
    if let Some(input_path) = args.input {
        println!("Reading hostnames from file: {}", input_path);
        let file_hostnames = std::fs::read_to_string(&input_path)
            .context(format!("Failed to read input file: {}", input_path))?
            .lines()
            .map(|line| line.trim().to_string())
            .filter(|line| !line.is_empty())
            .collect::<Vec<_>>();
        println!("Read {} hostnames from file", file_hostnames.len());
        hostnames.extend(file_hostnames);
    }

    if hostnames.is_empty() {
        println!("No hostnames provided. Please provide either a list of hostnames or a pattern.");
        return Ok(());
    }

    // Shuffle the hostnames
    if args.shuffle {
        println!("Shuffling hostnames...");
        hostnames.shuffle(&mut thread_rng());
    }
    
    println!("Resolving {} hostnames with a {} second timeout...", hostnames.len(), args.timeout);
    let start_time = Instant::now();

    // Initialize database
    println!("Initializing database...");
    let conn = Connection::open(&args.database)?;
    init_database(&conn)?;
    println!("Database initialized at: {}", args.database);

    // Create a new resolver using the system configuration
    println!("Creating DNS resolver...");
    let resolver = TokioAsyncResolver::tokio(ResolverConfig::default(), ResolverOpts::default());
    println!("DNS resolver created");

    let mut completed = 0;
    let total = hostnames.len();
    let mut results = Vec::with_capacity(total);

    // Process hostnames in batches
    println!("Starting DNS resolution...");
    for chunk in hostnames.chunks(args.concurrency) {
        println!("Processing batch of {} hostnames...", chunk.len());
        let mut futures = FuturesUnordered::new();
        
        // Create futures for this batch
        for hostname in chunk {
            futures.push(resolve_hostname(hostname.clone(), &resolver, timeout_duration));
        }

        // Process the batch
        while let Some(result) = futures.next().await {
            completed += 1;
            if result.ip_address.is_none() {
                println!("[{}/{}] {} - No IP addresses found", completed, total, result.hostname);
            } else {
                println!("[{}/{}] {} - Found IP: {}", completed, total, result.hostname, result.ip_address.as_ref().unwrap());
                if let Some(asn) = &result.asn {
                    println!("    ASN: {}", asn);
                    if let Some(as_name) = &result.as_name {
                        println!("    AS Name: {}", as_name);
                    }
                }
                results.push(result.clone());
                // Log to database
                if let Err(e) = save_result(&conn, &result) {
                    println!("Error logging to database: {}", e);
                }
            }
        }
    }

    // Now process HTTP requests for resolved hostnames
    println!("\nStarting HTTP checks...");
    let http_client = Client::builder()
        .user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/94.0.4606.52 Mobile/15E148 Safari/604.1")
        .danger_accept_invalid_certs(true)
        .timeout(Duration::from_secs(3))
        .build()?;

    let mut http_completed = 0;
    let http_total = results.len();
    let path = "/front/checkIp";

    // Process HTTP requests in batches
    for chunk in results.chunks(args.http_concurrency) {
        println!("Processing batch of {} HTTP requests...", chunk.len());
        let mut futures = FuturesUnordered::new();
        
        // Create futures for this batch
        for result in chunk {
            futures.push(check_http_endpoint(
                &http_client,
                &result.hostname,
                path,
                Duration::from_secs(3),
            ));
        }

        // Process the batch
        while let Some(result) = futures.next().await {
            http_completed += 1;
            if result.status_code == 200 {
                println!("[{}/{}] {} - {}: HTTP 200", 
                    http_completed, 
                    http_total, 
                    result.hostname, 
                    result.path
                );
                if let Some(response) = &result.response {
                    println!("    Response: {}", response);
                }
            }
            
            // Log to database
            if let Err(e) = save_http_result(&conn, &result) {
                println!("Error logging HTTP result to database: {}", e);
            }
        }
    }

    println!("\nProcessing completed in {:.2?}", start_time.elapsed());
    println!("Total hostnames processed: {}", total);
    println!("Successfully resolved: {}", results.len());
    println!("HTTP requests completed: {}", http_completed);

    Ok(())
}
