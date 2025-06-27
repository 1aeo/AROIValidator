import streamlit as st
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Tor Relay AROI Validator - Results Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_latest_results():
    """Load the latest validation results from JSON file"""
    results_dir = Path('validation_results')
    latest_file = results_dir / 'latest.json'
    
    if not latest_file.exists():
        return None
    
    try:
        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
        return None


def load_specific_results(filename):
    """Load specific validation results file"""
    results_dir = Path('validation_results')
    file_path = results_dir / filename
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
        return None


def list_available_results():
    """List all available results files"""
    results_dir = Path('validation_results')
    
    if not results_dir.exists():
        return []
    
    json_files = list(results_dir.glob('aroi_validation_*.json'))
    json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return json_files


def display_results_summary(data):
    """Display the validation results summary"""
    metadata = data.get('metadata', {})
    statistics = data.get('statistics', {})
    results = data.get('results', [])
    
    # Header with timestamp
    timestamp = metadata.get('timestamp', 'Unknown')
    st.subheader(f"📊 Validation Results - {timestamp}")
    
    # Summary metrics
    total_relays = metadata.get('total_relays', 0)
    valid_relays = metadata.get('valid_relays', 0)
    invalid_relays = metadata.get('invalid_relays', 0)
    success_rate = metadata.get('success_rate', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Relays", total_relays)
    with col2:
        st.metric("Valid AROI", valid_relays, f"{success_rate:.1f}%")
    with col3:
        st.metric("Invalid AROI", invalid_relays)
    with col4:
        color = "normal" if success_rate >= 80 else "inverse"
        st.metric("Success Rate", f"{success_rate:.1f}%", delta_color=color)
    
    # Proof type breakdown
    st.subheader("🔍 Proof Type Analysis")
    
    proof_types = statistics.get('proof_types', {})
    dns_rsa = proof_types.get('dns_rsa', {})
    uri_rsa = proof_types.get('uri_rsa', {})
    no_proof = proof_types.get('no_proof', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if dns_rsa.get('total', 0) > 0:
            dns_rate = dns_rsa.get('success_rate', 0)
            color = "🟢" if dns_rate >= 80 else "🟡" if dns_rate >= 50 else "🔴"
            st.write(f"{color} **DNS-RSA Proofs**")
            st.write(f"Valid: {dns_rsa.get('valid', 0)}/{dns_rsa.get('total', 0)} ({dns_rate:.1f}%)")
    
    with col2:
        if uri_rsa.get('total', 0) > 0:
            uri_rate = uri_rsa.get('success_rate', 0)
            color = "🟢" if uri_rate >= 80 else "🟡" if uri_rate >= 50 else "🔴"
            st.write(f"{color} **URI-RSA Proofs**")
            st.write(f"Valid: {uri_rsa.get('valid', 0)}/{uri_rsa.get('total', 0)} ({uri_rate:.1f}%)")
    
    with col3:
        if no_proof.get('total', 0) > 0:
            st.write("🔴 **No AROI Proof**")
            st.write(f"Count: {no_proof.get('total', 0)}")


def display_detailed_results(results):
    """Display detailed validation results"""
    if not results:
        return
    
    st.subheader("📋 Detailed Results")
    
    # Create DataFrame for better display
    df_data = []
    for result in results:
        df_data.append({
            'Nickname': result.get('nickname', 'Unknown'),
            'Fingerprint': result.get('fingerprint', 'Unknown')[:16] + '...',
            'Valid': '✅' if result['valid'] else '❌',
            'Proof Type': result.get('proof_type', 'None'),
            'Domain': result.get('domain', 'N/A'),
            'Error': result.get('error', '')[:50] + ('...' if len(result.get('error', '')) > 50 else '') if result.get('error') else ''
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Filters
    st.subheader("🔍 Filter Results")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Valid Only", "Invalid Only"],
            key="status_filter"
        )
    
    with col2:
        proof_types = list(set([r.get('proof_type') for r in results if r.get('proof_type')]))
        proof_filter = st.selectbox(
            "Proof Type",
            ["All"] + proof_types,
            key="proof_filter"
        )
    
    with col3:
        domains = list(set([r.get('domain') for r in results if r.get('domain')]))
        domain_filter = st.selectbox(
            "Domain",
            ["All"] + sorted(domains)[:20] if len(domains) > 20 else ["All"] + sorted(domains),
            key="domain_filter"
        )
    
    # Apply filters
    filtered_results = results
    
    if status_filter == "Valid Only":
        filtered_results = [r for r in filtered_results if r['valid']]
    elif status_filter == "Invalid Only":
        filtered_results = [r for r in filtered_results if not r['valid']]
    
    if proof_filter != "All":
        filtered_results = [r for r in filtered_results if r.get('proof_type') == proof_filter]
    
    if domain_filter != "All":
        filtered_results = [r for r in filtered_results if r.get('domain') == domain_filter]
    
    if filtered_results != results:
        st.write(f"Showing {len(filtered_results)} of {len(results)} results")
        
        # Create filtered DataFrame
        filtered_df_data = []
        for result in filtered_results:
            filtered_df_data.append({
                'Nickname': result.get('nickname', 'Unknown'),
                'Fingerprint': result.get('fingerprint', 'Unknown')[:16] + '...',
                'Valid': '✅' if result['valid'] else '❌',
                'Proof Type': result.get('proof_type', 'None'),
                'Domain': result.get('domain', 'N/A'),
                'Error': result.get('error', '')[:50] + ('...' if len(result.get('error', '')) > 50 else '') if result.get('error') else ''
            })
        
        filtered_df = pd.DataFrame(filtered_df_data)
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    # Expandable detailed view
    with st.expander("🔍 View Detailed Validation Information"):
        for i, result in enumerate(filtered_results[:50]):  # Limit to first 50 for performance
            st.subheader(f"Relay {i+1}: {result.get('nickname', 'Unknown')}")
            
            # Basic info
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Fingerprint:** `{result.get('fingerprint', 'Unknown')}`")
                st.write(f"**Valid:** {'✅ Yes' if result['valid'] else '❌ No'}")
            with col2:
                st.write(f"**Proof Type:** {result.get('proof_type', 'None')}")
                st.write(f"**Domain:** {result.get('domain', 'N/A')}")
            
            # Contact info with horizontal scroll
            if result.get('contact'):
                st.write("**Contact Information:**")
                st.code(result['contact'], language=None)
            
            # Error details
            if result.get('error'):
                st.error(f"**Error:** {result['error']}")
            
            if i < len(filtered_results) - 1 and i < 49:
                st.divider()
        
        if len(filtered_results) > 50:
            st.info(f"Showing first 50 results. Total filtered results: {len(filtered_results)}")


def main():
    # Header
    st.title("📊 Tor Relay AROI Validator - Results Viewer")
    st.markdown("View validation results from batch processing runs")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Results Files")
        
        # List available files
        available_files = list_available_results()
        
        if not available_files:
            st.warning("No validation results found. Run batch validation first.")
            st.markdown("""
            To generate results, run:
            ```bash
            python aroi_cli.py batch
            ```
            """)
        else:
            # File selection
            file_options = ["Latest Results"] + [f.name for f in available_files]
            selected_file = st.selectbox(
                "Select Results File",
                file_options,
                key="file_selection"
            )
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Auto-refresh latest results", value=True)
            
            if auto_refresh and selected_file == "Latest Results":
                st.write("🔄 Auto-refreshing every 30 seconds")
        
        st.divider()
        
        # Mode info
        st.subheader("🔧 Current Mode")
        st.info("**Viewer Mode**\nDisplay validation results without validation controls")
        
        st.subheader("ℹ️ About Viewer Mode")
        st.markdown("""
        This mode displays pre-computed validation results from batch runs:
        
        - **Read-only**: No validation controls
        - **Historical data**: View past validation runs
        - **Filtering**: Filter results by status, proof type, domain
        - **Export**: Download filtered results
        
        Use batch mode to generate new validation data.
        """)
    
    # Main content
    if not available_files:
        st.info("No validation results available. Run batch validation to generate data.")
        st.markdown("""
        ### Getting Started
        
        1. **Generate Results**: Run batch validation
           ```bash
           python aroi_cli.py batch
           ```
        
        2. **View Results**: Refresh this page to see the data
        
        3. **Schedule Regular Updates**: Set up a cron job for automated validation
           ```bash
           # Example: Run every 6 hours
           0 */6 * * * /path/to/python /path/to/aroi_cli.py batch
           ```
        """)
        return
    
    # Get selected file (with default)
    file_options = ["Latest Results"] + [f.name for f in available_files]
    selected_file = st.session_state.get('file_selection', "Latest Results")
    
    # Load and display results
    if selected_file == "Latest Results":
        data = load_latest_results()
    else:
        data = load_specific_results(selected_file)
    
    if not data:
        st.error("Failed to load validation results.")
        return
    
    # Display results
    display_results_summary(data)
    
    results = data.get('results', [])
    if results:
        display_detailed_results(results)
        
        # Export functionality
        st.subheader("📥 Export Results")
        
        # Prepare export data
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'source_file': selected_file,
            'total_relays': len(results),
            'valid_relays': sum(1 for r in results if r['valid']),
            'results': results
        }
        
        # Convert to JSON
        json_data = json.dumps(export_data, indent=2)
        
        # Create download
        st.download_button(
            label="📥 Download Results as JSON",
            data=json_data,
            file_name=f"aroi_results_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


if __name__ == "__main__":
    main()