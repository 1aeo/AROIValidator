"""
Unified AROI Validator Application
Supports interactive, batch, and viewer modes
"""
import sys
import json
from datetime import datetime
from pathlib import Path


def interactive_mode():
    """Interactive validation mode with start/stop controls"""
    import streamlit as st
    from ui_components import (
        display_summary_metrics,
        display_proof_type_analysis,
        display_results_table,
        display_validation_details
    )
    from validation_runner import (
        run_validation,
        calculate_statistics,
        save_results,
        load_results,
        list_result_files
    )
    
    st.set_page_config(
        page_title="Tor Relay AROI Validator - Interactive",
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
    
    # Define helper functions with access to st
    def start_interactive_validation():
        """Start validation in interactive mode"""
        st.session_state.validation_in_progress = True
        st.session_state.validation_results = []
        
        # Create progress container
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(current, total, result):
                # Check if stopped
                if st.session_state.validation_stopped:
                    return
                
                # Update progress
                progress = current / total
                progress_bar.progress(progress)
                status_text.text(f"Validating: {current}/{total} - {result.get('nickname', 'Unknown')}")
                
                # Add result
                st.session_state.validation_results.append(result)
            
            def stop_check():
                return st.session_state.validation_stopped
            
            # Run validation
            results = run_validation(progress_callback=progress_callback, stop_check=stop_check)
            
            # Update final results
            st.session_state.validation_results = results
            st.session_state.validation_in_progress = False
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ Validation complete! Processed {len(results)} relays.")
            st.rerun()
    
    def display_interactive_results():
        """Display results for interactive mode"""
        results = st.session_state.validation_results
        
        if not results:
            return
        
        # Calculate statistics
        stats = calculate_statistics(results)
        
        # Summary section
        st.subheader("📊 Validation Results Summary")
        display_summary_metrics(
            stats['total_relays'],
            stats['valid_relays'],
            stats['invalid_relays'],
            stats['success_rate']
        )
        
        # Proof type analysis
        display_proof_type_analysis(results)
        
        # Detailed results table
        st.subheader("📋 Detailed Results")
        df, filtered_results = display_results_table(results, show_filters=True)
        
        # Validation details
        if filtered_results:
            display_validation_details(filtered_results)
    
    def export_results():
        """Export current results to file"""
        if st.session_state.validation_results:
            file_path = save_results(st.session_state.validation_results)
            st.success(f"✅ Results exported to {file_path}")
    
    # Header
    st.title("🧅 Tor Relay AROI Validator - Interactive Mode")
    st.markdown("Full interactive validation with start/stop controls and real-time tracking")
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Validation controls
        st.subheader("Validation")
        
        # Start button
        if not st.session_state.validation_in_progress:
            if st.button("▶️ Start Validation", type="primary", use_container_width=True):
                st.session_state.validation_stopped = False
                start_interactive_validation()
        
        # Stop button  
        if st.session_state.validation_in_progress:
            if st.button("⏹️ Stop Validation", type="secondary", use_container_width=True):
                st.session_state.validation_stopped = True
                st.session_state.validation_in_progress = False
                st.rerun()
        
        st.divider()
        
        # Export controls
        st.subheader("Export")
        if st.session_state.validation_results:
            if st.button("📥 Export Results", use_container_width=True):
                export_results()
        
        # Clear results
        if st.session_state.validation_results:
            if st.button("🗑️ Clear Results", use_container_width=True):
                st.session_state.validation_results = []
                st.session_state.validation_stopped = False
                st.rerun()
        
        st.divider()
        
        # Mode info
        st.subheader("🔧 Current Mode")
        st.info("**Interactive Mode**\nFull validation controls with real-time tracking")
    
    # Main content area
    if st.session_state.validation_results:
        display_interactive_results()
    else:
        st.info("👆 Click 'Start Validation' in the sidebar to begin validating Tor relays")


def viewer_mode():
    """View pre-computed validation results"""
    import streamlit as st
    from ui_components import (
        display_summary_metrics,
        display_proof_type_analysis,
        display_results_table,
        display_validation_details
    )
    from validation_runner import load_results, list_result_files
    
    st.set_page_config(
        page_title="Tor Relay AROI Validator - Results Viewer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📊 Tor Relay AROI Validator - Results Viewer")
    st.markdown("View pre-computed validation results")
    
    # Sidebar file selector
    with st.sidebar:
        st.header("📁 Result Files")
        
        result_files = list_result_files()
        
        if not result_files:
            st.warning("No validation results found. Run a validation first.")
            return
        
        # File selector
        file_options = {
            "Latest Results": "latest.json"
        }
        
        for file_path in result_files[:10]:  # Limit to 10 most recent
            timestamp = file_path.stem.replace('aroi_validation_', '')
            try:
                dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                display_name = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                display_name = file_path.name
            file_options[display_name] = file_path.name
        
        selected_display = st.selectbox(
            "Select Results File",
            options=list(file_options.keys()),
            key="file_selector"
        )
        
        selected_file = file_options[selected_display]
        
        st.divider()
        st.subheader("🔧 Current Mode")
        st.info("**Viewer Mode**\nView validation results without controls")
    
    # Define helper function with access to st
    def display_viewer_results(data):
        """Display results for viewer mode"""
        metadata = data.get('metadata', {})
        statistics = data.get('statistics', {})
        results = data.get('results', [])
        
        # Header with timestamp
        timestamp = metadata.get('timestamp', 'Unknown')
        st.subheader(f"📊 Validation Results - {timestamp}")
        
        # Summary metrics
        display_summary_metrics(
            statistics['total_relays'],
            statistics['valid_relays'],
            statistics['invalid_relays'],
            statistics['success_rate']
        )
        
        # Proof type analysis
        display_proof_type_analysis(results)
        
        # Detailed results table
        st.subheader("📋 Detailed Results")
        df, filtered_results = display_results_table(results, show_filters=True)
        
        # Validation details
        if filtered_results:
            display_validation_details(filtered_results)
        
        # Export button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("📥 Export as JSON"):
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(data, indent=2),
                    file_name=f"aroi_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if df is not None and st.button("📊 Export as CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"aroi_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # Load and display selected results
    data = load_results(selected_file)
    
    if not data:
        st.error(f"Error loading results from {selected_file}")
        return
    
    display_viewer_results(data)


def batch_mode():
    """Batch validation mode for automated processing"""
    from validation_runner import (
        run_validation,
        calculate_statistics,
        save_results
    )
    
    print("AROI Batch Validator")
    print("=" * 50)
    print(f"Starting validation at {datetime.now().isoformat()}")
    
    # Check for limit parameter
    import os
    limit = int(os.environ.get('BATCH_LIMIT', 100))  # Default to 100 for reasonable performance
    
    # Run validation with progress output
    def progress_callback(current, total, result):
        status = "✓" if result['valid'] else "✗"
        print(f"[{current}/{total}] {status} {result.get('nickname', 'Unknown')}")
    
    results = run_validation(progress_callback=progress_callback, limit=limit)
    
    # Save results
    file_path = save_results(results)
    
    # Print summary
    stats = calculate_statistics(results)
    print("\n" + "=" * 50)
    print("VALIDATION COMPLETE")
    print(f"Total Relays: {stats['total_relays']}")
    print(f"Valid AROI: {stats['valid_relays']} ({stats['success_rate']:.1f}%)")
    print(f"Invalid AROI: {stats['invalid_relays']}")
    print(f"Results saved to: {file_path}")
    
    # Also output JSON to stdout for piping
    output = {
        'timestamp': datetime.now().isoformat(),
        'statistics': stats,
        'results_file': str(file_path)
    }
    print("\n" + json.dumps(output, indent=2))




def main():
    """Main entry point - determine mode from command line or default to interactive"""
    # Check for command line mode argument
    mode = "interactive"  # Default mode
    
    # Check if --mode argument is provided
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