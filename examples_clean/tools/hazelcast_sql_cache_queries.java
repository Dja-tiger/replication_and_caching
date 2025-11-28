// Техномир: SQL-подобные запросы к распределённому кэшу
public class ProductSearchService {
    private final HazelcastInstance hz;

    public List<Product> findExpensiveProducts(double minPrice) {
        IMap<Long, Product> products = hz.getMap("products");

        // SQL предикат
        SqlPredicate predicate = new SqlPredicate(
            "price > " + minPrice + " AND available = true"
        );

        return new ArrayList<>(products.values(predicate));
    }

    public List<Product> findByCategory(String category) {
        // Индексированный поиск
        IMap<Long, Product> products = hz.getMap("products");
        products.addIndex(IndexType.HASH, "category");

        Predicate predicate = Predicates.equal("category", category);
        return new ArrayList<>(products.values(predicate));
    }
}

// Производительность: поиск по 1М записей < 100ms