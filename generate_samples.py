from run_lift_simulation import run_lift_simulation
import json

def generate_sample(name, brand, cat, city, context):
    print(f"\n--- {name} Sample ---")
    data = {"business_context": context}
    result = run_lift_simulation(brand, cat, city, data)
    print(f"Template Used: {result['template_used']}")
    print(f"Gaps: {len(result['gaps'])}")
    print(f"Strengths: {len(result['strengths'])}")
    print(f"Remediation: {len(result['remediation'])}")

    # Check for contamination
    remediation_text = str(result['remediation']).lower()
    if cat == 'fitness gym':
        forbidden = ['shipping', 'size guide', 'product schema']
    elif cat == 'online fashion store':
        forbidden = ['healthclub', 'trainer credential', 'class schedule']
    elif cat == 'dental clinic':
        forbidden = ['shipping', 'size guide', 'healthclub', 'class schedule']

    contamination = [f for f in forbidden if f in remediation_text]
    print(f"Contamination: {'None' if not contamination else f'FOUND: {contamination}'}")
    return result

# Fitness
generate_sample(
    "Fitness",
    "Capital Arena Fitness Club",
    "fitness gym",
    "Islamabad",
    "4.5 rating, swimming pool, sauna"
)

# Ecommerce
generate_sample(
    "Ecommerce",
    "MEME Official Store",
    "online fashion store",
    "Pakistan",
    "Shopify store, fashion retail, American Express accepted"
)

# Dental
generate_sample(
    "Dental",
    "Dental Solutions Islamabad",
    "dental clinic",
    "Islamabad",
    "Braces, implants, root canal, hygiene focused"
)
