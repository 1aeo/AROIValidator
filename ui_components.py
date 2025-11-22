"""
Shared UI components for AROI Validator application
"""
import streamlit as st
import pandas as pd


def display_summary_metrics(total_relays, valid_relays, invalid_relays, success_rate):
    """Display summary metrics in a consistent format"""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Relays", total_relays)
    with col2:
        st.metric("Valid AROI", valid_relays, f"{success_rate:.1f}%")
    with col3:
        st.metric("Invalid AROI", invalid_relays, f"{(invalid_relays/total_relays*100):.1f}%" if total_relays > 0 else "0%")
    with col4:
        color = "normal" if success_rate >= 80 else "inverse"
        st.metric("Success Rate", f"{success_rate:.1f}%", delta_color=color)


def display_proof_type_analysis(results):
    """Display proof type analysis breakdown"""
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


def display_results_table(results, show_filters=True):
    """Display results in a formatted table with optional filters"""
    if not results:
        return None, None
    
    # Create DataFrame
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
    
    filtered_results = results
    if show_filters:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "Valid Only", "Invalid Only"],
                key="status_filter"
            )
            if status_filter == "Valid Only":
                filtered_results = [r for r in results if r['valid']]
            elif status_filter == "Invalid Only":
                filtered_results = [r for r in results if not r['valid']]
        
        with col2:
            proof_types = list(set([r.get('proof_type') for r in results if r.get('proof_type')]))
            proof_filter = st.selectbox(
                "Proof Type",
                ["All"] + proof_types,
                key="proof_filter"
            )
            if proof_filter != "All":
                filtered_results = [r for r in filtered_results if r.get('proof_type') == proof_filter]
        
        with col3:
            domains = list(set([r.get('domain') for r in results if r.get('domain')]))
            domain_filter = st.selectbox(
                "Domain",
                ["All"] + sorted(domains)[:20] if len(domains) > 20 else ["All"] + sorted(domains),
                key="domain_filter"
            )
            if domain_filter != "All":
                filtered_results = [r for r in filtered_results if r.get('domain') == domain_filter]
    
    # Display filtered DataFrame
    if filtered_results != results:
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
        df = pd.DataFrame(filtered_df_data)
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    return df, filtered_results


def display_validation_details(results):
    """Display expandable validation details for each relay"""
    with st.expander("🔍 Validation Details", expanded=False):
        for idx, result in enumerate(results[:50]):  # Limit to first 50 for performance
            with st.container():
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    status = "✅ Valid" if result['valid'] else "❌ Invalid"
                    st.write(f"**{status}**")
                    st.write(f"**{result.get('nickname', 'Unknown')}**")
                
                with col2:
                    st.write(f"**Fingerprint:** {result.get('fingerprint', 'Unknown')}")
                    if result.get('proof_type'):
                        st.write(f"**Proof Type:** {result['proof_type']}")
                    if result.get('domain'):
                        st.write(f"**Domain:** {result['domain']}")
                    
                    if result.get('validation_steps'):
                        st.write("**Validation Steps:**")
                        for step in result['validation_steps']:
                            status_icon = "✅" if step['success'] else "❌"
                            st.write(f"  {status_icon} {step['step']}")
                            if step.get('details'):
                                st.write(f"    → {step['details']}")
                    
                    if result.get('error'):
                        st.error(f"**Error:** {result['error']}")
                
                if idx < len(results) - 1:
                    st.divider()