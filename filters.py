def filtrer(offres):
    result = []
    for o in offres:
        titre = o["titre"].lower()

        if "stage" not in titre:
            continue

        if not any(k in titre for k in [
            "dev", "dévelop", "software", "informatique"
        ]):
            continue

        result.append(o)

    return result
