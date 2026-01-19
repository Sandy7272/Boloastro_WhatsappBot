def normalize_city(c):
    c=c.lower().strip()
    mapping={
        "mumbai":"Mumbai",
        "bombay":"Mumbai",
        "pune":"Pune",
        "poona":"Pune",
        "delhi":"Delhi"
    }
    return mapping.get(c,c.title())
