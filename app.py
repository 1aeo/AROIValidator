import streamlit as st
import pandas as pd
import json
import io
from aroi_validator import AROIValidator

def display_results_summary():
    """Display the validation results summary and details"""
    results = st.session_state.validation_results
    
    if not results:
        return
    
    # Summary statistics
    total_relays = len(results)
    valid_relays = sum(1 for r in results if r['valid'])
    invalid_relays = total_relays - valid_relays
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Relays", total_relays)
    with col2:
        st.metric("Valid AROI", valid_relays, delta=f"{(valid_relays/total_relays*100):.1f}%")
    with col3:
        st.metric("Invalid AROI", invalid_relays, delta=f"{(invalid_relays/total_relays*100):.1f}%")
    
    # Color-coded validation status summary
    st.subheader("🎨 Color-Coded Status Overview")
    
    # Calculate validation statistics by categories
    dns_rsa_valid = sum(1 for r in results if r.get('proof_type') == 'dns-rsa' and r['valid'])
    dns_rsa_total = sum(1 for r in results if r.get('proof_type') == 'dns-rsa')
    uri_rsa_valid = sum(1 for r in results if r.get('proof_type') == 'uri-rsa' and r['valid'])
    uri_rsa_total = sum(1 for r in results if r.get('proof_type') == 'uri-rsa')
    missing_fields = sum(1 for r in results if 'Missing AROI fields' in str(r.get('error', '')))
    unsupported_version = sum(1 for r in results if 'Unsupported ciissversion' in str(r.get('error', '')))
    unsupported_proof = sum(1 for r in results if 'Unsupported proof type' in str(r.get('error', '')))
    
    # Create visual status summary with color coding
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Validation by Proof Type:**")
        
        # DNS-RSA validation
        if dns_rsa_total > 0:
            dns_success_rate = (dns_rsa_valid / dns_rsa_total) * 100
            if dns_success_rate >= 80:
                color = "🟢"
            elif dns_success_rate >= 50:
                color = "🟡"
            else:
                color = "🔴"
            st.write(f"{color} DNS-RSA: {dns_rsa_valid}/{dns_rsa_total} ({dns_success_rate:.1f}%)")
        
        # URI-RSA validation
        if uri_rsa_total > 0:
            uri_success_rate = (uri_rsa_valid / uri_rsa_total) * 100
            if uri_success_rate >= 80:
                color = "🟢"
            elif uri_success_rate >= 50:
                color = "🟡"
            else:
                color = "🔴"
            st.write(f"{color} URI-RSA: {uri_rsa_valid}/{uri_rsa_total} ({uri_success_rate:.1f}%)")
    
    with col2:
        st.write("**Common Issues:**")
        
        if missing_fields > 0:
            st.write(f"🔴 Missing Fields: {missing_fields} relays")
        
        if unsupported_version > 0:
            st.write(f"🟠 Unsupported Version: {unsupported_version} relays")
        
        if unsupported_proof > 0:
            st.write(f"🟠 Unsupported Proof Type: {unsupported_proof} relays")
        
        if missing_fields == 0 and unsupported_version == 0 and unsupported_proof == 0:
            st.write("🟢 No common configuration issues found")
    
    # Overall health indicator
    overall_success_rate = (valid_relays / total_relays) * 100 if total_relays > 0 else 0
    
    if overall_success_rate >= 80:
        health_color = "🟢"
        health_status = "Excellent"
    elif overall_success_rate >= 60:
        health_color = "🟡"
        health_status = "Good"
    elif overall_success_rate >= 40:
        health_color = "🟠"
        health_status = "Fair"
    else:
        health_color = "🔴"
        health_status = "Poor"
    
    st.info(f"{health_color} **Overall Validation Health: {health_status}** ({overall_success_rate:.1f}% success rate)")

def main():
    st.title("🔍 Tor Relay AROI Validator")
    st.markdown("Validate Tor relay AROI (Autonomous Relay Operator Identity) proofs through DNS and URI verification")
    
    # Initialize session state
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = None
    if 'validation_in_progress' not in st.session_state:
        st.session_state.validation_in_progress = False
    
    # Main layout with sections
    st.header("🚀 Validation Setup")
    
    # Data source selection
    data_source = st.radio(
        "Choose data source:",
        ["Fetch from Onionoo API", "Upload JSON file"],
        help="Fetch relay data automatically from Tor's Onionoo API or upload your own relay data file"
    )
    
    if data_source == "Fetch from Onionoo API":
        st.info("This will fetch relay data from https://onionoo.torproject.org/details")
        
        if st.button("🔄 Fetch and Validate Relays", disabled=st.session_state.validation_in_progress):
            run_validation()
            
    else:  # Upload JSON file
        st.info("Upload a JSON file containing relay data with fingerprint, nickname, and contact fields")
        
        uploaded_file = st.file_uploader(
            "Choose a JSON file",
            type="json",
            help="File should contain relay data in Onionoo format"
        )
        
        if uploaded_file is not None:
            try:
                file_content = uploaded_file.read()
                relay_data = json.loads(file_content)
                
                # Validate file structure
                if isinstance(relay_data, dict) and "relays" in relay_data:
                    relays = relay_data["relays"]
                elif isinstance(relay_data, list):
                    relays = relay_data
                else:
                    st.error("Invalid file format. Expected JSON with 'relays' array or direct array of relays.")
                    return
                
                st.success(f"✅ Loaded {len(relays)} relays from file")
                
                if st.button("🔍 Validate Uploaded Data", disabled=st.session_state.validation_in_progress):
                    run_validation(relays)
                    
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file. Please check the file format.")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    # Create a persistent results container
    st.divider()
    results_container = st.container()
    
    with results_container:
        st.header("📊 Validation Results")
        
        # Show status and progress in a placeholder that doesn't clear
        status_placeholder = st.empty()
        results_placeholder = st.empty()
        
        with status_placeholder.container():
            if st.session_state.get('validation_in_progress', False):
                st.info("Validation in progress...")
                if st.session_state.validation_results and len(st.session_state.validation_results) > 0:
                    current_count = len(st.session_state.validation_results)
                    valid_count = sum(1 for r in st.session_state.validation_results if r.get('valid', False))
                    st.success(f"Progress: {current_count} relays processed, {valid_count} valid")
            else:
                if st.session_state.validation_results is None or len(st.session_state.validation_results) == 0:
                    st.info("No validation results yet. Start validation above to see results here.")
        
        # Results content in its own placeholder
        with results_placeholder.container():
            if st.session_state.validation_results and len(st.session_state.validation_results) > 0:
                display_results_summary()
    
    # Export section (only show if results exist)
    if st.session_state.validation_results is not None and len(st.session_state.validation_results) > 0:
        st.divider()
        export_results()

@st.fragment
def perform_validation(relay_data=None):
    """Perform the actual validation work"""
    try:
        validator = AROIValidator()
        
        # Get relay data
        if relay_data is None:
            relays = validator.fetch_relay_data()
        else:
            relays = relay_data
        
        # Process each relay
        for i, relay in enumerate(relays):
            result = validator.validate_relay(relay)
            st.session_state.validation_results.append(result)
            
            # Update progress every relay
            current_count = len(st.session_state.validation_results)
            valid_count = sum(1 for r in st.session_state.validation_results if r.get('valid', False))
            st.write(f"Processing relay {current_count}/{len(relays)}: {valid_count} valid so far")
            
    except Exception as e:
        st.error(f"Validation failed: {str(e)}")
    finally:
        st.session_state.validation_in_progress = False

def run_validation(relay_data=None):
    """Start validation process"""
    st.session_state.validation_in_progress = True
    st.session_state.validation_results = []
    
    # Start the validation in a fragment
    perform_validation(relay_data)



def export_results():
    """Export validation results"""
    if st.session_state.validation_results is None:
        st.info("👆 No validation results to export. Use the 'Validate' tab to start validation.")
        return
    
    st.header("📁 Export Validation Results")
    
    results = st.session_state.validation_results
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "Export Format",
            ["JSON", "CSV"],
            help="Choose the format for exporting results"
        )
    
    with col2:
        export_filter = st.selectbox(
            "Export Filter",
            ["All Results", "Valid Only", "Invalid Only"],
            help="Choose which results to export"
        )
    
    # Apply export filter
    if export_filter == "Valid Only":
        export_data = [r for r in results if r['valid']]
    elif export_filter == "Invalid Only":
        export_data = [r for r in results if not r['valid']]
    else:
        export_data = results
    
    # Generate export data
    if export_format == "JSON":
        export_content = json.dumps(export_data, indent=2)
        file_extension = "json"
        mime_type = "application/json"
    else:  # CSV
        df = pd.DataFrame(export_data)
        export_content = df.to_csv(index=False)
        file_extension = "csv"
        mime_type = "text/csv"
    
    # Display preview
    st.subheader("📋 Export Preview")
    st.info(f"Exporting {len(export_data)} records in {export_format} format")
    
    if export_format == "JSON":
        st.json(export_data[:3] if len(export_data) > 3 else export_data)
        if len(export_data) > 3:
            st.caption("... (showing first 3 records)")
    else:
        st.dataframe(pd.DataFrame(export_data).head(), use_container_width=True)
        if len(export_data) > 5:
            st.caption("... (showing first 5 records)")
    
    # Download button
    filename = f"aroi_validation_results.{file_extension}"
    
    st.download_button(
        label=f"📥 Download {export_format} File",
        data=export_content,
        file_name=filename,
        mime=mime_type,
        help=f"Download validation results as {export_format} file"
    )
    
    # Summary statistics
    st.subheader("📊 Export Summary")
    total_exported = len(export_data)
    valid_exported = sum(1 for r in export_data if r['valid'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Records to Export", total_exported)
    with col2:
        st.metric("Valid Records", valid_exported)

if __name__ == "__main__":
    main()
