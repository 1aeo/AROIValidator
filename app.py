"""
Ultra-Simplified AROI Validator
All-in-one application with parallel validation support
"""
import sys
import json
import os
from datetime import datetime
from pathlib import Path


def interactive_mode():
    """Interactive validation mode with Streamlit UI"""
    import streamlit as st
    import pandas as pd
    from aroi_validator_parallel import (
        run_validation, calculate_statistics, save_results,
        load_results, list_result_files
    )
    
    st.set_page_config(
        page_title="Tor Relay AROI Validator",
        page_icon="🧅",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = []
    if 'validation_in_progress' not in st.session_state:
        st.session_state.validation_in_progress = False
    if 'validation_stopped' not in st.session_state:
        st.session_state.validation_stopped = False
    
    # Helper functions
    def start_validation():
        """Start validation with parallel processing"""
        st.session_state.validation_in_progress = True
        st.session_state.validation_results = []
        
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Get configuration
            use_parallel = st.session_state.get('use_parallel', True)
            max_workers = st.session_state.get('max_workers', 10)
            limit = st.session_state.get('validation_limit', 100)
            
            def progress_callback(current, total, result):
                if st.session_state.validation_stopped:
                    return
                
                progress = current / total
                progress_bar.progress(progress)
                status = "✓" if result['valid'] else "✗"
                status_text.text(f"Validating: {current}/{total} - {status} {result.get('nickname', 'Unknown')}")
                
                st.session_state.validation_results.append(result)
            
            def stop_check():
                return st.session_state.validation_stopped
            
            # Run validation with parallel processing
            results = run_validation(
                progress_callback=progress_callback,
                stop_check=stop_check,
                limit=limit,
                parallel=use_parallel,
                max_workers=max_workers
            )
            
            st.session_state.validation_results = results
            st.session_state.validation_in_progress = False
            
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ Validation complete! Processed {len(results)} relays.")
            st.rerun()
    
    def display_results():
        """Display validation results"""
        results = st.session_state.validation_results
        if not results:
            return
        
        stats = calculate_statistics(results)
        
        # Summary metrics
        st.subheader("📊 Validation Results")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Relays", stats['total_relays'])
        with col2:
            st.metric("Valid AROI", stats['valid_relays'], f"{stats['success_rate']:.1f}%")
        with col3:
            st.metric("Invalid AROI", stats['invalid_relays'])
        with col4:
            color = "🟢" if stats['success_rate'] >= 80 else "🟡" if stats['success_rate'] >= 50 else "🔴"
            st.metric("Success Rate", f"{color} {stats['success_rate']:.1f}%")
        
        # Proof type breakdown
        st.subheader("🔍 Proof Type Analysis")
        proof_types = stats['proof_types']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            dns = proof_types['dns_rsa']
            if dns['total'] > 0:
                st.write(f"**DNS-RSA**: {dns['valid']}/{dns['total']} ({dns['success_rate']:.1f}%)")
        with col2:
            uri = proof_types['uri_rsa']
            if uri['total'] > 0:
                st.write(f"**URI-RSA**: {uri['valid']}/{uri['total']} ({uri['success_rate']:.1f}%)")
        with col3:
            no_proof = proof_types['no_proof']
            if no_proof['total'] > 0:
                st.write(f"**No Proof**: {no_proof['total']}")
        
        # Results table
        st.subheader("📋 Detailed Results")
        df_data = []
        for result in results:
            df_data.append({
                'Nickname': result.get('nickname', 'Unknown'),
                'Fingerprint': result.get('fingerprint', '')[:16] + '...',
                'Valid': '✅' if result['valid'] else '❌',
                'Proof Type': result.get('proof_type', 'None'),
                'Domain': result.get('domain', 'N/A'),
                'Error': result.get('error', '')[:50] if result.get('error') else ''
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Header
    st.title("🧅 Tor Relay AROI Validator")
    st.markdown("Validate Tor relay operator identities with parallel processing")
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Validation configuration
        st.subheader("Configuration")
        
        st.session_state.use_parallel = st.checkbox(
            "Use Parallel Processing",
            value=True,
            help="Enable parallel validation for faster processing"
        )
        
        if st.session_state.use_parallel:
            st.session_state.max_workers = st.slider(
                "Worker Threads",
                min_value=1,
                max_value=20,
                value=10,
                help="Number of parallel validation threads"
            )
        
        st.session_state.validation_limit = st.number_input(
            "Max Relays to Validate",
            min_value=1,
            max_value=1000,
            value=100,
            step=10,
            help="Limit the number of relays to validate"
        )
        
        st.divider()
        
        # Validation controls
        st.subheader("Validation")
        
        if not st.session_state.validation_in_progress:
            if st.button("▶️ Start Validation", type="primary", use_container_width=True):
                st.session_state.validation_stopped = False
                start_validation()
        else:
            if st.button("⏹️ Stop Validation", type="secondary", use_container_width=True):
                st.session_state.validation_stopped = True
                st.session_state.validation_in_progress = False
                st.rerun()
        
        st.divider()
        
        # Export controls
        if st.session_state.validation_results:
            st.subheader("Export")
            if st.button("📥 Save Results", use_container_width=True):
                file_path = save_results(st.session_state.validation_results)
                st.success(f"Saved to {file_path}")
            
            if st.button("🗑️ Clear Results", use_container_width=True):
                st.session_state.validation_results = []
                st.session_state.validation_stopped = False
                st.rerun()
    
    # Main content area
    if st.session_state.validation_results:
        display_results()
    else:
        st.info("👆 Click 'Start Validation' to begin. Parallel processing is enabled by default for faster validation!")


def viewer_mode():
    """View saved validation results"""
    import streamlit as st
    import pandas as pd
    from aroi_validator_parallel import load_results, list_result_files
    
    st.set_page_config(
        page_title="AROI Validator - Results Viewer",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 AROI Validation Results Viewer")
    
    # File selector
    result_files = list_result_files()
    
    if not result_files:
        st.warning("No validation results found. Run a validation first.")
        return
    
    file_options = ["latest.json"] + [f.name for f in result_files[:10]]
    selected_file = st.selectbox("Select Results File", file_options)
    
    # Load and display results
    data = load_results(selected_file)
    if not data:
        st.error(f"Error loading {selected_file}")
        return
    
    # Display statistics
    stats = data.get('statistics', {})
    metadata = data.get('metadata', {})
    
    st.subheader(f"Results from {metadata.get('timestamp', 'Unknown')}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Relays", stats.get('total_relays', 0))
    with col2:
        st.metric("Valid AROI", stats.get('valid_relays', 0))
    with col3:
        st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
    
    # Results table
    st.subheader("Detailed Results")
    results = data.get('results', [])
    
    df_data = []
    for result in results:
        df_data.append({
            'Nickname': result.get('nickname', 'Unknown'),
            'Valid': '✅' if result['valid'] else '❌',
            'Proof Type': result.get('proof_type', 'None'),
            'Domain': result.get('domain', 'N/A')
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def batch_mode():
    """Batch validation mode for automation"""
    from aroi_validator_parallel import (
        run_validation, calculate_statistics, save_results
    )
    
    print("AROI Batch Validator (Parallel Processing)")
    print("=" * 50)
    print(f"Starting validation at {datetime.now().isoformat()}")
    
    # Configuration from environment
    limit = int(os.environ.get('BATCH_LIMIT', 100))
    use_parallel = os.environ.get('PARALLEL', 'true').lower() == 'true'
    max_workers = int(os.environ.get('MAX_WORKERS', 10))
    
    if use_parallel:
        print(f"Using parallel processing with {max_workers} workers")
    
    # Progress callback
    def progress_callback(current, total, result):
        status = "✓" if result['valid'] else "✗"
        print(f"[{current}/{total}] {status} {result.get('nickname', 'Unknown')}")
    
    # Run validation
    results = run_validation(
        progress_callback=progress_callback,
        limit=limit,
        parallel=use_parallel,
        max_workers=max_workers
    )
    
    # Save and report
    file_path = save_results(results)
    stats = calculate_statistics(results)
    
    print("\n" + "=" * 50)
    print("VALIDATION COMPLETE")
    print(f"Total Relays: {stats['total_relays']}")
    print(f"Valid AROI: {stats['valid_relays']} ({stats['success_rate']:.1f}%)")
    print(f"Invalid AROI: {stats['invalid_relays']}")
    print(f"Results saved to: {file_path}")
    
    # JSON output for automation
    output = {
        'timestamp': datetime.now().isoformat(),
        'statistics': stats,
        'results_file': str(file_path)
    }
    print("\n" + json.dumps(output, indent=2))


def main():
    """Main entry point with mode selection"""
    mode = "interactive"
    
    # Check for command line mode
    if "--mode" in sys.argv:
        mode_index = sys.argv.index("--mode") + 1
        if mode_index < len(sys.argv):
            mode = sys.argv[mode_index]
    
    # Route to appropriate mode
    if mode == "batch":
        batch_mode()
    elif mode == "viewer":
        viewer_mode()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()