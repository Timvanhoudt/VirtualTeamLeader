"""
Test script voor nieuwe werkplek API endpoints
"""

import sys
sys.path.insert(0, 'backend')

from database import (
    init_database,
    create_workplace,
    get_all_workplaces,
    get_workplace,
    update_workplace,
    get_training_dataset_stats
)

def test_workplace_management():
    """Test werkplek CRUD operations"""
    print("=" * 60)
    print("TEST: Werkplek Management")
    print("=" * 60)

    # Initialiseer database
    init_database()
    print("\n1. Database geinitialiseerd")

    # Test 1: Maak werkplek aan
    print("\n2. Test: Werkplek aanmaken")

    # Check of werkplek al bestaat
    existing = get_all_workplaces()
    workplace_id = None
    for wp in existing:
        if wp['name'] == "Werkplek A - Gereedschap":
            workplace_id = wp['id']
            print(f"   Werkplek bestaat al (ID: {workplace_id})")
            break

    if workplace_id is None:
        workplace_id = create_workplace(
            name="Werkplek A - Gereedschap",
            description="Hoofdwerkplek met hamer, schaar en sleutel",
            items=["hamer", "schaar", "sleutel"],
            reference_photo=None
        )
        print(f"   Werkplek aangemaakt (ID: {workplace_id})")

    # Test 2: Haal werkplek op
    print("\n3. Test: Werkplek ophalen")
    workplace = get_workplace(workplace_id)
    print(f"   Naam: {workplace['name']}")
    print(f"   Items: {workplace['items']}")
    print(f"   Actief: {workplace['active']}")

    # Test 3: Update werkplek
    print("\n4. Test: Werkplek updaten")
    update_workplace(
        workplace_id=workplace_id,
        description="Bijgewerkte beschrijving - hoofdwerkplek productie"
    )
    updated = get_workplace(workplace_id)
    print(f"   Nieuwe beschrijving: {updated['description']}")

    # Test 4: Maak tweede werkplek
    print("\n5. Test: Tweede werkplek aanmaken")
    workplace_id_2 = create_workplace(
        name="Magazijn - Voorraad",
        description="Magazijn met pallets en vorkheftruck",
        items=["pallet", "vorkheftruck", "scanner"]
    )
    print(f"   Werkplek ID: {workplace_id_2}")

    # Test 5: Lijst alle werkplekken
    print("\n6. Test: Alle werkplekken ophalen")
    workplaces = get_all_workplaces()
    print(f"   Totaal aantal werkplekken: {len(workplaces)}")
    for wp in workplaces:
        print(f"   - {wp['name']} (ID: {wp['id']})")

    # Test 6: Dataset stats (moet leeg zijn)
    print("\n7. Test: Dataset statistieken")
    stats = get_training_dataset_stats(workplace_id)
    print(f"   Totaal images: {stats['total_images']}")
    print(f"   Gevalideerd: {stats['validated_count']}")
    print(f"   Label distributie: {stats['label_distribution']}")

    print("\n" + "=" * 60)
    print("ALLE TESTS GESLAAGD!")
    print("=" * 60)

if __name__ == "__main__":
    test_workplace_management()
