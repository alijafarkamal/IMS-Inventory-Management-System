from dataclasses import dataclass, asdict
from typing import List, Optional
from uuid import uuid4

class CategoryNotFoundError(Exception):
    """Raised when a category with the given id does not exist."""
    pass


class CategoryAlreadyExistsError(Exception):
    """Raised when trying to create a category with a name that already exists."""
    pass


@dataclass
class Category:
    id: str
    name: str
    description: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class CategoryService:
    """
    Simple in-memory dummy category service.
    Methods:
      - list_categories()
      - get_category(category_id)
      - create_category(name, description=None)
      - update_category(category_id, name=None, description=None)
      - delete_category(category_id)
    This is intended for development/testing only.
    """

    def __init__(self):
        # simple in-memory store: list of Category
        self._categories: List[Category] = []
        # seed with some dummy categories
        self._seed()

    def _seed(self):
        if not self._categories:
            self._categories.extend([
                Category(id=str(uuid4()), name="Electronics", description="Electronic items"),
                Category(id=str(uuid4()), name="Furniture", description="Home and office furniture"),
                Category(id=str(uuid4()), name="Stationery", description="Office supplies and stationery"),
            ])

    def list_categories(self) -> List[Category]:
        """Return a list of all categories."""
        return list(self._categories)

    def get_category(self, category_id: str) -> Category:
        """Return a category by id or raise CategoryNotFoundError."""
        for c in self._categories:
            if c.id == category_id:
                return c
        raise CategoryNotFoundError(f"Category with id '{category_id}' not found")

    def create_category(self, name: str, description: Optional[str] = None) -> Category:
        """Create a new category. Names must be unique (case-insensitive)."""
        normalized = name.strip().lower()
        for c in self._categories:
            if c.name.strip().lower() == normalized:
                raise CategoryAlreadyExistsError(f"Category with name '{name}' already exists")
        new_cat = Category(id=str(uuid4()), name=name.strip(), description=description)
        self._categories.append(new_cat)
        return new_cat

    def update_category(self, category_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Category:
        """
        Update name and/or description of a category. Name uniqueness is enforced.
        Returns the updated Category.
        """
        category = self.get_category(category_id)  # will raise if not found

        if name is not None:
            normalized = name.strip().lower()
            for c in self._categories:
                if c.id != category_id and c.name.strip().lower() == normalized:
                    raise CategoryAlreadyExistsError(f"Category with name '{name}' already exists")
            category.name = name.strip()

        if description is not None:
            category.description = description

        return category

    def delete_category(self, category_id: str) -> None:
        """Delete a category by id. Raises CategoryNotFoundError if not found."""
        for i, c in enumerate(self._categories):
            if c.id == category_id:
                del self._categories[i]
                return
        raise CategoryNotFoundError(f"Category with id '{category_id}' not found")


# Example usage (for quick manual testing; remove in production)
if __name__ == "__main__":
    svc = CategoryService()
    print("Seeded categories:")
    for cat in svc.list_categories():
        print(cat.to_dict())

    print("\nCreating a new category 'Tools'")
    tools = svc.create_category("Tools", "Hand and power tools")
    print(tools.to_dict())

    print("\nUpdating 'Tools' description")
    updated = svc.update_category(tools.id, description="All kinds of tools")
    print(updated.to_dict())

    print("\nDeleting 'Tools'")
    svc.delete_category(tools.id)
    print("Remaining categories:", [c.to_dict() for c in svc.list_categories()])