from typing import List
import numpy as np
import re
import spacy
from scipy.spatial import distance as di

RU_INDEX_FILE = "./../a-crawling/crawling/crawling/spiders/pages/index.txt"
RU_LEMMAS_FILE = "./../b-tokens/ru_lemmas.txt"
RU_LEMMAS_TF_IDF_FOLDER = "./../d-tf-idf/ru-lemmas/"


class VectorSearch:
    # hardcoded config
    def __init__(self, lang="RU"):
        self.nlp_en = spacy.load("en_core_web_sm")
        self.nlp_ru = spacy.load("ru_core_news_sm")

        self.lang = lang

        index_file_name = RU_INDEX_FILE
        tf_idf_folder = RU_LEMMAS_TF_IDF_FOLDER

        ## INIT
        # key - web page id (believed to be int), self.pages[idx] - url for that web page
        self.pages = dict()

        # key - file (web page) id, file_lemmas[idx] - lemmas for file with given id
        page_lemmas = dict()

        # mapping of idxes 
        # key - new value of page index (matching to the row in matrix), value - initial idx of file from {index_file_name}
        # why needed? 1) real idxes start from 1, 2) real idxes has 'windows' in values range
        self.idxs_mapping = dict()

        ## READ self.pages
        with open(index_file_name, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                index_enrty = line.split(',')

                page_url = index_enrty[0]
                page_lang = index_enrty[1].upper()
                html_file_name = index_enrty[2]

                file_idx_match = re.search(r'(\d+)-.*\.html$', html_file_name)
                file_idx = int(file_idx_match.group(1))

                # language filter
                if page_lang == self.lang:
                    self.pages[file_idx] = page_url

        print(f"URLs count = {len(self.pages)}")

        ## READ LEMMAS
        page_idxes = self.pages.keys()
        count = 0

        for page_idx in page_idxes:
            self.idxs_mapping[count] = page_idx
            count = count + 1

            with open(f"{tf_idf_folder}{page_idx}.txt", 'r', encoding='utf-8') as file:
                lemmas = []
                lines = file.readlines()
                for line in lines:
                    tf_idf_entry = line.split(' ')
                    lemmas.append(tf_idf_entry[0])

                page_lemmas[page_idx] = lemmas

        print(f"Lemmas per page dictionary size = {len(page_lemmas)}")
        print(f"Indexes mappings dictionary size = {len(self.idxs_mapping)}")

        ## COLLECT ALL LEMMAS
        self.all_lemmas = []

        all_lemmas_set = set()
        for lemmas in page_lemmas.values():
            all_lemmas_set.update(lemmas)

        # list of all existing lemmas
        self.all_lemmas = list(all_lemmas_set)
        print(f"All lemmas count = {len(self.all_lemmas)}")

        ## MATRIX
        self.pages_count = len(self.idxs_mapping)
        self.lemmas_count = len(self.all_lemmas)

        # matrix
        # row num - page idx, row value - vector for page
        # column - lemma
        self.matrix = np.zeros((self.pages_count, self.lemmas_count))

        ## INIT MATRIX
        for i in range(0, self.pages_count):
            # trash - нужно не запутаться где какой индекс взять
            with open(f"{tf_idf_folder}{self.idxs_mapping[i]}.txt", 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for line in lines:
                    lemma, _, tf_idf = line.split(' ')
                    if lemma in self.all_lemmas:
                        # column
                        lemma_index_in_matrix = self.all_lemmas.index(lemma)
                        self.matrix[i][lemma_index_in_matrix] = float(tf_idf)
                    else:
                        print(f"Opps '{lemma}' not found in all_lemmas. matrix corrupted")

    def __get_tokens(self, text, lang):
        if (lang == "RU"):
            doc = self.nlp_ru(text)
        else:
            doc = self.nlp_en(text)

        return [w for w in doc if (w.is_alpha and not w.is_stop)]

    def __query_to_vector(self, query: str, lang) -> np.ndarray:
        vector = np.zeros(self.lemmas_count)
        tokens = self.__get_tokens(query, lang=lang)
        # print(tokens)
        for token in tokens:
            lemma = token.lemma_
            if lemma in self.all_lemmas:
                lemma_index_in_matrix = self.all_lemmas.index(lemma)
                vector[lemma_index_in_matrix] = 1
                # print(lemma_index_in_matrix)

        return vector

    # returns list of tuples, sorted by distance
    # (url, distance)
    def search(self, query: str, lang="RU") -> List:
        query_vector = self.__query_to_vector(query, lang)
        relevant_pages = dict()

        for page_row_idx, page_vector in enumerate(self.matrix):
            # cosine similarity between 2 vectors
            # https://medium.com/@milana.shxanukova15/cosine-distance-and-cosine-similarity-a5da0e4d9ded
            if sum(page_vector) > 0:
                similarity = 1 - di.cosine(query_vector, page_vector)
                if similarity > 0:
                    relevant_pages[page_row_idx] = similarity

        # sort by distance
        relevant_pages_sorted = sorted(relevant_pages.items(), key=lambda item: item[1], reverse=True)

        # file idx - initial url
        search_result = [(self.pages[self.idxs_mapping[idx_to_distance[0]]], idx_to_distance[1])
                         for idx_to_distance in relevant_pages_sorted]

        return search_result
