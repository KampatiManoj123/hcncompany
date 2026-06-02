"""
HCN Database Seeder
Run this to populate sample products into MongoDB
Usage: python init_db.py
"""
from pymongo import MongoClient
from datetime import datetime

def seed():
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
        client.server_info()
        db = client['hcn_db']
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("   Make sure MongoDB is running on localhost:27017")
        return

    # Clear existing
    db.products.delete_many({})
    print("🗑️  Cleared existing products")

    products = [
        # Dish Care
        {
            'name': 'HCN Dishwash Liquid 1L',
            'category': 'Dish Care',
            'price': 110.00,
            'mrp': 140.00,
            'stock': 200,
            'description': 'Powerful dishwash liquid that cuts through grease and leaves dishes sparkling clean. Gentle on hands with a pleasant lime fragrance.',
            'features': ['Cuts through tough grease', 'Gentle on hands', 'Pleasant lime fragrance', 'Eco-friendly formula', '1 Litre pack'],
            'weight': '1L',
            'sku': 'HCN-DC-001',
            'image': '',
            'is_new': False,
            'is_bestseller': True,
            'created_at': datetime.now()
        },
        {
            'name': 'HCN Dishwash Bar 200g',
            'category': 'Dish Care',
            'price': 35.00,
            'mrp': 45.00,
            'stock': 500,
            'description': 'Concentrated dishwash bar for effective cleaning of utensils. Long-lasting and economical.',
            'features': ['Long lasting', 'Removes food residue', 'Anti-bacterial', '200g bar'],
            'weight': '200g',
            'sku': 'HCN-DC-002',
            'image': '',
            'is_new': True,
            'is_bestseller': False,
            'created_at': datetime.now()
        },
        # Kitchen Care
        {
            'name': 'HCN Kitchen Degreaser Spray',
            'category': 'Kitchen Care',
            'price': 160.00,
            'mrp': 200.00,
            'stock': 150,
            'description': 'Heavy-duty kitchen degreaser spray that effortlessly removes oil, grease and grime from all kitchen surfaces.',
            'features': ['Removes heavy grease', 'Safe on all surfaces', 'No scrubbing needed', 'Fresh fragrance', '500ml trigger spray'],
            'weight': '500ml',
            'sku': 'HCN-KC-001',
            'image': '',
            'is_new': False,
            'is_bestseller': True,
            'created_at': datetime.now()
        },
        {
            'name': 'HCN Orange Degreaser 500ml',
            'category': 'Kitchen Care',
            'price': 150.00,
            'mrp': 185.00,
            'stock': 120,
            'description': 'Natural orange-based degreaser for kitchen surfaces. Powerful cleaning with a fresh citrus scent.',
            'features': ['Natural orange extract', 'Biodegradable', 'Multi-surface safe', 'Refreshing citrus smell'],
            'weight': '500ml',
            'sku': 'HCN-KC-002',
            'image': '',
            'is_new': True,
            'is_bestseller': False,
            'created_at': datetime.now()
        },
        # Laundry Care
        {
            'name': 'HCN Liquid Detergent Ultra 1L',
            'category': 'Laundry Care',
            'price': 320.00,
            'mrp': 399.00,
            'stock': 100,
            'description': 'Ultra-concentrated liquid detergent for brilliant white and bright colours. Works in both top load and front load machines.',
            'features': ['Ultra concentrated formula', 'Works in all machines', 'Removes tough stains', 'Color safe', 'Fresh fragrance', '1 Litre'],
            'weight': '1L',
            'sku': 'HCN-LC-001',
            'image': '',
            'is_new': True,
            'is_bestseller': False,
            'created_at': datetime.now()
        },
        {
            'name': 'HCN Fabric Conditioner 1L',
            'category': 'Laundry Care',
            'price': 210.00,
            'mrp': 260.00,
            'stock': 80,
            'description': 'Premium fabric conditioner that leaves clothes soft, fresh and static-free. Long-lasting fragrance for up to 48 hours.',
            'features': ['Softens fabric', 'Anti-static', '48hr fragrance', 'Color enhancer'],
            'weight': '1L',
            'sku': 'HCN-LC-002',
            'image': '',
            'is_new': False,
            'is_bestseller': True,
            'created_at': datetime.now()
        },
        # Bathroom Care
        {
            'name': 'HCN Bathroom Cleaner 500ml',
            'category': 'Bathroom Care',
            'price': 140.00,
            'mrp': 175.00,
            'stock': 180,
            'description': 'Powerful bathroom cleaner with 10X cleaning action. Removes tough stains, limescale and kills 99.9% germs.',
            'features': ['10X cleaning power', 'Kills 99.9% germs', 'Removes limescale', 'Thick gel formula', 'Fresh fragrance'],
            'weight': '500ml',
            'sku': 'HCN-BC-001',
            'image': '',
            'is_new': True,
            'is_bestseller': False,
            'created_at': datetime.now()
        },
        {
            'name': 'HCN Toilet Cleaner 1L',
            'category': 'Bathroom Care',
            'price': 95.00,
            'mrp': 120.00,
            'stock': 250,
            'description': 'Thick gel toilet cleaner that clings to the bowl for deep cleaning. Kills bacteria and removes stains effectively.',
            'features': ['Thick gel formula', 'Kills bacteria', 'Removes yellow stains', 'Fresh pine fragrance', '1 Litre'],
            'weight': '1L',
            'sku': 'HCN-BC-002',
            'image': '',
            'is_new': False,
            'is_bestseller': True,
            'created_at': datetime.now()
        },
        # Hand Wash
        {
            'name': 'HCN Herbal Hand Wash 500ml',
            'category': 'Hand Wash',
            'price': 110.00,
            'mrp': 140.00,
            'stock': 300,
            'description': 'Gentle herbal hand wash with neem and tulsi extracts. Kills 99.9% germs while keeping hands soft and moisturized.',
            'features': ['Neem & Tulsi extracts', 'Kills 99.9% germs', 'Moisturizes hands', 'pH balanced', 'No parabens'],
            'weight': '500ml',
            'sku': 'HCN-HW-001',
            'image': '',
            'is_new': True,
            'is_bestseller': False,
            'created_at': datetime.now()
        },
        {
            'name': 'HCN Rose Hand Wash 250ml',
            'category': 'Hand Wash',
            'price': 65.00,
            'mrp': 85.00,
            'stock': 400,
            'description': 'Delicate rose-scented hand wash with moisturizing ingredients for soft and clean hands all day.',
            'features': ['Rose fragrance', 'Moisturizing formula', 'Gentle on skin', '250ml pump bottle'],
            'weight': '250ml',
            'sku': 'HCN-HW-002',
            'image': '',
            'is_new': False,
            'is_bestseller': True,
            'created_at': datetime.now()
        },
    ]

    result = db.products.insert_many(products)
    print(f"✅ Inserted {len(result.inserted_ids)} sample products")
    print("\n📦 Products added:")
    for p in products:
        print(f"   • {p['name']} — ₹{p['price']}")

    print("\n🎉 Database seeded successfully!")
    print("   Visit http://localhost:5000 to see your store")
    print("   Visit http://localhost:5000/admin to manage products")

if __name__ == '__main__':
    seed()
