import streamlit as st
import pandas as pd
import json
import io
from aroi_validator import AROIValidator

def main():
    st.title("🔍 Tor Relay AROI Validator")
    st.markdown("Validate Tor relay AROI (Autonomous Relay Operator Identity) proofs through DNS and URI verification")
    
    # Initialize session state
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = None
    if 'validation_in_progress' not in st.session_state:
        st.session_state.validation_in_progress = False
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🚀 Validate", "📊 Results", "📁 Export"])
    
    with tab1:
        st.header("Data Source")
        
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
    
    with tab2:
        display_results()
    
    with tab3:
        export_results()

def run_validation(relay_data=None):
    """Run AROI validation with progress tracking"""
    st.session_state.validation_in_progress = True
    
    try:
        validator = AROIValidator()
        
        # Create progress containers
        progress_container = st.container()
        with progress_container:
            st.info("🚀 Starting validation process...")
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Fetch or use provided relay data
        if relay_data is None:
            status_text.text("📡 Fetching relay data from Onionoo...")
            relays = validator.fetch_relay_data()
            st.success(f"✅ Fetched {len(relays)} relays from Onionoo")
        else:
            relays = relay_data
            st.success(f"✅ Using {len(relays)} relays from uploaded file")
        
        # Validate relays
        status_text.text("🔍 Validating AROI proofs...")
        results = []
        
        # Create container for detailed validation steps
        validation_details = st.expander("Detailed Validation Steps", expanded=True)
        
        for i, relay in enumerate(relays):
            # Update progress
            progress = (i + 1) / len(relays)
            progress_bar.progress(progress)
            nickname = relay.get('nickname', 'Unknown')
            fingerprint = relay.get('fingerprint', 'N/A')
            status_text.text(f"🔍 Validating relay {i + 1}/{len(relays)}: {nickname}")
            
            with validation_details:
                st.write(f"**Relay {i + 1}: {nickname}** (`{fingerprint[:16]}...`)")
                
                # Create columns for checklist
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    checklist_container = st.container()
                
                # Validate individual relay with step tracking
                result = validator.validate_relay_with_steps(relay, checklist_container)
                results.append(result)
                
                with col2:
                    if result['valid']:
                        st.success("✅ Valid")
                    else:
                        st.error("❌ Invalid")
                
                if i < len(relays) - 1:  # Don't add divider after last relay
                    st.divider()
        
        # Store results in session state
        st.session_state.validation_results = results
        
        # Clear progress indicators
        progress_container.empty()
        
        # Show completion message
        total_relays = len(results)
        valid_relays = sum(1 for r in results if r['valid'])
        invalid_relays = total_relays - valid_relays
        
        st.success(f"✅ Validation complete! {valid_relays} valid, {invalid_relays} invalid out of {total_relays} relays")
        
        # Switch to results tab
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Validation failed: {str(e)}")
    finally:
        st.session_state.validation_in_progress = False

def display_results():
    """Display validation results in an interactive table"""
    if st.session_state.validation_results is None:
        st.info("👆 No validation results yet. Use the 'Validate' tab to start validation.")
        return
    
    results = st.session_state.validation_results
    
    # Summary statistics
    st.header("📊 Validation Summary")
    
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
    
    # Filters
    st.header("🔍 Filter Results")
    
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Validation Status",
            ["All", "Valid", "Invalid"],
            help="Filter relays by validation status"
        )
    
    with col2:
        proof_type_filter = st.selectbox(
            "Proof Type",
            ["All"] + list(set(r.get('proof_type', 'N/A') for r in results if r.get('proof_type'))),
            help="Filter relays by proof type"
        )
    
    search_term = st.text_input(
        "🔍 Search",
        placeholder="Search by nickname, fingerprint, or domain...",
        help="Search across nickname, fingerprint, and domain fields"
    )
    
    # Apply filters
    filtered_results = results.copy()
    
    if status_filter == "Valid":
        filtered_results = [r for r in filtered_results if r['valid']]
    elif status_filter == "Invalid":
        filtered_results = [r for r in filtered_results if not r['valid']]
    
    if proof_type_filter != "All":
        filtered_results = [r for r in filtered_results if r.get('proof_type') == proof_type_filter]
    
    if search_term:
        search_lower = search_term.lower()
        filtered_results = [
            r for r in filtered_results
            if search_lower in r.get('nickname', '').lower()
            or search_lower in r.get('fingerprint', '').lower()
            or search_lower in str(r.get('domain', '')).lower()
        ]
    
    # Display results table
    st.header(f"📋 Results ({len(filtered_results)} relays)")
    
    if not filtered_results:
        st.warning("No relays match the current filters.")
        return
    
    # Convert to DataFrame for better display
    df_data = []
    for result in filtered_results:
        df_data.append({
            'Status': '✅ Valid' if result['valid'] else '❌ Invalid',
            'Nickname': result.get('nickname', 'N/A'),
            'Fingerprint': result.get('fingerprint', 'N/A')[:16] + '...' if result.get('fingerprint') else 'N/A',
            'Domain': result.get('domain', 'N/A'),
            'Proof Type': result.get('proof_type', 'N/A'),
            'Version': result.get('ciissversion', 'N/A'),
            'Error': result.get('error', 'None')[:50] + '...' if result.get('error') and len(result.get('error', '')) > 50 else result.get('error', 'None')
        })
    
    df = pd.DataFrame(df_data)
    
    # Display with styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Status': st.column_config.TextColumn(width='small'),
            'Fingerprint': st.column_config.TextColumn(width='medium'),
            'Error': st.column_config.TextColumn(width='large')
        }
    )
    
    # Detailed error view
    st.header("🔍 Detailed Error Analysis")
    
    invalid_results = [r for r in filtered_results if not r['valid']]
    if invalid_results:
        selected_relay = st.selectbox(
            "Select relay for detailed error information:",
            options=range(len(invalid_results)),
            format_func=lambda i: f"{invalid_results[i].get('nickname', 'Unknown')} ({invalid_results[i].get('fingerprint', 'N/A')[:16]}...)"
        )
        
        if selected_relay is not None:
            relay = invalid_results[selected_relay]
            
            with st.expander("📄 Full Error Details", expanded=True):
                st.json({
                    'Fingerprint': relay.get('fingerprint'),
                    'Nickname': relay.get('nickname'),
                    'Domain': relay.get('domain'),
                    'Proof Type': relay.get('proof_type'),
                    'CIISS Version': relay.get('ciissversion'),
                    'Valid': relay.get('valid'),
                    'Error': relay.get('error')
                })
    else:
        st.success("🎉 No errors found in the current filter results!")

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
