from vector_search import VectorSearch

if __name__ == '__main__':
    vector_search = VectorSearch()
    result = vector_search.search(query="понос")

    print(result)