"""
add_unique_constraints_to_inventory
"""
from yoyo import step

__depends__ = {'20251212_03_6eVqZ-seed-datos-desarrollo'}

steps = [
    step(
        """
        ALTER TABLE inventory_items
        ADD CONSTRAINT uq_inventory_items_name UNIQUE (name);
        """,
        """
        ALTER TABLE inventory_items
        DROP INDEX uq_inventory_items_name;
        """
    ),
    step(
        """
        ALTER TABLE products
        ADD CONSTRAINT uq_products_name UNIQUE (name);
        """,
        """
        ALTER TABLE products
        DROP INDEX uq_products_name;
        """
    )
]
