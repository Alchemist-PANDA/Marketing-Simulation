import re

def main():
    with open('geo_audit_agent/graph_nodes.py', 'r') as f:
        content = f.read()
    
    # We need to inject patch_business_data_for_dental right after the business_data extraction in gap_analyst_node
    
    old_code = """    brand_name = state.get("brand_name", "")
    category = state.get("category", "")
    city = state.get("city", "")
    business_data = state.get("business_data", {})

    # Run the audit - this uses get_template internally"""
    
    new_code = """    brand_name = state.get("brand_name", "")
    category = state.get("category", "")
    city = state.get("city", "")
    business_data = state.get("business_data", {})
    
    if "dental" in category.lower() or "dentist" in category.lower():
        business_data = patch_business_data_for_dental(business_data)

    # Run the audit - this uses get_template internally"""
    
    content = content.replace(old_code, new_code)
    
    with open('geo_audit_agent/graph_nodes.py', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    main()
