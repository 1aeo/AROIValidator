import streamlit as st
import pandas as pd
from aroi_validator import AROIValidator
import json
import time

# Configure page
st.set_page_config(
    page_title="Tor Relay AROI Validator - Interactive",
    page_icon="🧅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize validator
if 'validator' not in st.session_state:
    st.session_state.validator = AROIValidator()

# Initialize session state variables
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = []
if 'validation_in_progress' not in st.session_state:
    st.session_state.validation_in_progress = False
if 'validation_stopped' not in st.session_state:
    st.session_state.validation_stopped = False


def display_results_summary():
    """Display the validation results summary and details"""
    if not st.session_state.validation_results:
        return
        
    results = st.session_state.validation_results
    
    # Summary metrics
    st.subheader("📊 Validation Results Summary")
    
    total_relays = len(results)
    valid_relays = sum(1 for r in results if r['valid'])
    invalid_relays = total_relays - valid_relays
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Relays", total_relays)
    with col2:
        st.metric("Valid AROI", valid_relays, f"{(valid_relays/total_relays*100):.1f}%")
    with col3:
        st.metric("Invalid AROI", invalid_relays, f"{(invalid_relays/total_relays*100):.1f}%")
    with col4:
        success_rate = (valid_relays / total_relays) * 100
        color = "normal" if success_rate >= 80 else "inverse"
        st.metric("Success Rate", f"{success_rate:.1f}%", delta_color=color)
    
    # Proof type breakdown
    st.subheader("🔍 Proof Type Analysis")
    
    dns_rsa_results = [r for r in results if r.get('proof_type') == 'dns-rsa']
    uri_rsa_results = [r for r in results if r.get('proof_type') == 'uri-rsa']
    no_proof_results = [r for r in results if not r.get('proof_type')]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if dns_rsa_results:
            dns_valid = sum(1 for r in dns_rsa_results if r['valid'])
            dns_total = len(dns_rsa_results)
            dns_rate = (dns_valid / dns_total) * 100
            color = "🟢" if dns_rate >= 80 else "🟡" if dns_rate >= 50 else "🔴"
            st.write(f"{color} **DNS-RSA Proofs**")
            st.write(f"Valid: {dns_valid}/{dns_total} ({dns_rate:.1f}%)")
    
    with col2:
        if uri_rsa_results:
            uri_valid = sum(1 for r in uri_rsa_results if r['valid'])
            uri_total = len(uri_rsa_results)
            uri_rate = (uri_valid / uri_total) * 100
            color = "🟢" if uri_rate >= 80 else "🟡" if uri_rate >= 50 else "🔴"
            st.write(f"{color} **URI-RSA Proofs**")
            st.write(f"Valid: {uri_valid}/{uri_total} ({uri_rate:.1f}%)")
    
    with col3:
        if no_proof_results:
            st.write("🔴 **No AROI Proof**")
            st.write(f"Count: {len(no_proof_results)}")


def main():
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
                run_validation()
        
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
        
        st.subheader("ℹ️ About")
        st.markdown("""
        This tool validates AROI (Autonomous Relay Operator Identity) proofs for Tor relays by:
        
        1. **Fetching** relay data from Onionoo API
        2. **Parsing** AROI tokens from contact fields  
        3. **Validating** DNS-RSA and URI-RSA proofs
        4. **Verifying** cryptographic signatures
        
        **Supported proof types:**
        - `dns-rsa`: DNS TXT record verification
        - `uri-rsa`: HTTP URI verification
        """)
    
    # Main content area
    if st.session_state.validation_in_progress:
        st.info("🔄 Validation in progress... Use the stop button to halt early and preserve partial results.")
    
    # Show results if available
    if st.session_state.validation_results:
        display_results_summary()
        
        # Detailed results
        st.subheader("📋 Detailed Results")
        
        # Create DataFrame for better display
        df_data = []
        for result in st.session_state.validation_results:
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
        
        # Expandable detailed view
        with st.expander("🔍 View Detailed Validation Steps"):
            for i, result in enumerate(st.session_state.validation_results):
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
                
                # Validation steps
                if result.get('steps'):
                    st.write("**Validation Steps:**")
                    for step in result['steps']:
                        status = "✅" if step['status'] == 'success' else "❌" if step['status'] == 'error' else "⏳"
                        st.write(f"{status} {step['message']}")
                
                # Error details
                if result.get('error'):
                    st.error(f"**Error:** {result['error']}")
                
                if i < len(st.session_state.validation_results) - 1:
                    st.divider()
    
    elif not st.session_state.validation_in_progress:
        # Welcome message
        st.info("👋 Welcome to Interactive Mode! Click 'Start Validation' in the sidebar to begin validating Tor relay AROI proofs.")
        
        st.subheader("🎯 What This Tool Does")
        st.markdown("""
        This validator checks if Tor relays have properly configured AROI (Autonomous Relay Operator Identity) proofs:
        
        - **DNS-RSA**: Verifies a TXT record in DNS containing a cryptographic proof
        - **URI-RSA**: Verifies a proof document served over HTTPS
        
        The validation process includes DNSSEC verification for enhanced security.
        """)


def run_validation(relay_data=None):
    """Run AROI validation with progress tracking"""
    if st.session_state.validation_in_progress:
        return
        
    st.session_state.validation_in_progress = True
    st.session_state.validation_stopped = False
    
    try:
        # Create containers for live updates
        status_container = st.container()
        live_results_placeholder = st.empty()
        progress_container = st.container()
        
        with status_container:
            st.info("🔄 Starting validation process...")
        
        # Fetch relay data if not provided
        if relay_data is None:
            with status_container:
                st.info("📡 Fetching relay data from Onionoo API...")
            relays = st.session_state.validator.fetch_relay_data()
        else:
            relays = relay_data
        
        if not relays:
            st.error("❌ No relay data available")
            return
        
        with status_container:
            st.success(f"✅ Found {len(relays)} relays to validate")
        
        # Initialize results list
        results = []
        
        # Progress tracking
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Validate each relay with live updates
        for i, relay in enumerate(relays):
            # Check if validation was stopped
            if st.session_state.validation_stopped:
                break
                
            # Update progress
            progress = (i + 1) / len(relays)
            progress_bar.progress(progress)
            status_text.text(f"Validating relay {i+1}/{len(relays)}: {relay.get('nickname', 'Unknown')}")
            
            # Validate relay with detailed steps
            with progress_container:
                step_container = st.container()
                result = st.session_state.validator.validate_relay_with_steps(relay, step_container)
            
            results.append(result)
            
            # Update session state with current results before updating UI
            st.session_state.validation_results = results.copy()
            
            # Update live results summary in placeholder
            valid_count = sum(1 for r in results if r['valid'])
            total_count = len(results)
            with live_results_placeholder.container():
                # Show current results summary
                st.subheader("📊 Live Results Summary")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Processed", total_count, f"of {len(relays)}")
                with col2:
                    st.metric("Valid AROI", valid_count, f"{(valid_count/total_count*100):.1f}%")
                with col3:
                    invalid_count = total_count - valid_count
                    st.metric("Invalid AROI", invalid_count, f"{(invalid_count/total_count*100):.1f}%")
                
                # Show proof type breakdown if we have results
                if results:
                    dns_rsa_valid = sum(1 for r in results if r.get('proof_type') == 'dns-rsa' and r['valid'])
                    dns_rsa_total = sum(1 for r in results if r.get('proof_type') == 'dns-rsa')
                    uri_rsa_valid = sum(1 for r in results if r.get('proof_type') == 'uri-rsa' and r['valid'])
                    uri_rsa_total = sum(1 for r in results if r.get('proof_type') == 'uri-rsa')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if dns_rsa_total > 0:
                            dns_rate = (dns_rsa_valid / dns_rsa_total) * 100
                            color = "🟢" if dns_rate >= 80 else "🟡" if dns_rate >= 50 else "🔴"
                            st.write(f"{color} DNS-RSA: {dns_rsa_valid}/{dns_rsa_total} ({dns_rate:.1f}%)")
                    
                    with col2:
                        if uri_rsa_total > 0:
                            uri_rate = (uri_rsa_valid / uri_rsa_total) * 100
                            color = "🟢" if uri_rate >= 80 else "🟡" if uri_rate >= 50 else "🔴"
                            st.write(f"{color} URI-RSA: {uri_rsa_valid}/{uri_rsa_total} ({uri_rate:.1f}%)")
        
        # Final update to session state
        st.session_state.validation_results = results
        
        # Clear progress indicators
        progress_container.empty()
        
        # Show completion message
        total_relays = len(results)
        valid_relays = sum(1 for r in results if r['valid'])
        invalid_relays = total_relays - valid_relays
        
        if st.session_state.get('validation_stopped', False):
            st.warning(f"⏹️ Validation stopped! {valid_relays} valid, {invalid_relays} invalid out of {total_relays} relays processed")
        else:
            st.success(f"✅ Validation complete! {valid_relays} valid, {invalid_relays} invalid out of {total_relays} relays")
        
    except Exception as e:
        st.error(f"❌ Validation failed: {str(e)}")
    finally:
        st.session_state.validation_in_progress = False


def export_results():
    """Export validation results"""
    if not st.session_state.validation_results:
        st.warning("⚠️ No results to export")
        return
    
    # Prepare export data
    export_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'total_relays': len(st.session_state.validation_results),
        'valid_relays': sum(1 for r in st.session_state.validation_results if r['valid']),
        'results': st.session_state.validation_results
    }
    
    # Convert to JSON
    json_data = json.dumps(export_data, indent=2)
    
    # Create download
    st.download_button(
        label="📥 Download JSON",
        data=json_data,
        file_name=f"aroi_validation_results_{time.strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )


if __name__ == "__main__":
    main()