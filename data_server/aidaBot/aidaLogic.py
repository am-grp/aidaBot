# import sys
import json
import datetime
from elasticsearch import Elasticsearch
# from fuzzywuzzy import fuzz
from fuzzywuzzy import process

host = input ('ElasticSearch Host IP ')

es = Elasticsearch([{'host': host, 'port': 9200}])
index = 'aida2'
author_index = 'authors2'
threshold = 85
dsc_authors_index = 'authors'
dsc_conferences_index = 'conferences'


def authors_name(authors):
    msg = ''
    if len(authors) > 1:
        msg = ' et al.'
    for a in authors:
        if a['order'] == 1:
            # print(a['name'])
            msg = a['name'] + msg
    return msg


def lst(sub, obj, ins, num=5, order=1):
    # print('sub:', sub, ' ins:', ins, ' order:', order, ' obj:', obj)
    result = json.dumps({'result': 'Query not implemented yet'})
    num = int(num)
    result_lst = []
    sub_fields = ['authors.id', '', 'conferenceseriesid', 'authors.affiliation.keyword', 'cso_enhanced_topics.keyword']
    obj_fields = ['cso_enhanced_topics.keyword', 'conferenceseriesid', 'authors.affiliation.keyword', 'authors.id']
    order_fields = ['citationcount', 'citationcount_5']
    sub_field = sub_fields[int(sub) - 1]
    obj_field = 0
    if 0 < int(obj) < 5:
        obj_field = obj_fields[int(obj) - 1]

    # elenca i primi x per numero di pubblicazioni con x != papers e nessuna istanza
    if sub != '2' and ins == 'all' and order == '1':
        res = es.search(index=index, body={"size": 0, "track_total_hits": 'true', "query": {"match_all": {}},
                                           "aggs": {"names": {"terms": {"field": sub_field, "size": num}}}})
        a = res['aggregations']['names']['buckets']
        for i in a:
            result_lst.append({"name": i["key"], "papers": i["doc_count"]})
        result = {"lst": result_lst, 'result': 'ok'}

    # elenca i primi x per numero di citazioni(entrambi i casi) con x != papers e nessuna istanza
    elif sub != '2' and ins == 'all' and (order == '2' or order == '4'):
        n = int(int(order) / 2 - 1)
        res = es.search(index=index, body={"size": 0, "track_total_hits": 'true', "query": {"match_all": {}}, "aggs": {
            "names": {"terms": {"field": sub_field, "size": 50000},
                      "aggs": {"the_sum": {"sum": {"field": order_fields[n]}}, "citation_bucket_sort": {
                          "bucket_sort": {"sort": [{"the_sum": {"order": "desc"}}], "size": num}}}}}})
        a = res['aggregations']['names']['buckets']
        for i in a:
            result_lst.append({"name": i["key"], "papers": i["doc_count"], "citations": i["the_sum"]["value"]})
        result = {"lst": result_lst, 'result': 'ok'}

    # elenca i primi x per numero di pubblicazioni negli ultimi 5 anni con x != papers e nessuna istanza
    elif sub != '2' and ins == 'all' and order == '3':
        year = datetime.datetime.now().year
        res = es.search(index=index, body={"size": 0, "track_total_hits": 'true',
                                           "query": {"range": {"year": {"gte": year - 5, "lte": year}}},
                                           "aggs": {"names": {"terms": {"field": sub_field, "size": num}}}})
        a = res['aggregations']['names']['buckets']
        for i in a:
            result_lst.append({"name": i["key"], "papers": i["doc_count"]})
        result = {"lst": result_lst, 'result': 'ok'}

    # elenca i primi x per numero di pubblicazioni con x != papers e istanza di tipo obj qualsiasi
    # tranne il caso in cui sub=autore e obj=organizzazione
    elif sub != '2' and ins != 'all' and order == '1' and not (sub == '1' and obj == '3'):
        res = es.search(index=index,
                        body={"size": 0, "track_total_hits": 'true', "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"names": {"terms": {"field": sub_field, "size": num}}}})
        a = res['aggregations']['names']['buckets']
        for i in a:
            result_lst.append({"name": i["key"], "papers": i["doc_count"]})
        result = {"lst": result_lst, 'result': 'ok'}

    # elenca i primi x per numero di citazioni(entrambi i casi) con x != papers e istanza di tipo obj qualsiasi
    # tranne il caso in cui sub=autore e obj=organizzazione
    elif sub != '2' and ins != 'all' and (order == '2' or order == '4') and not (sub == '1' and obj == '3'):
        n = int(int(order) / 2 - 1)
        res = es.search(index=index,
                        body={"size": 0, "track_total_hits": 'true', "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"names": {"terms": {"field": sub_field, "size": 50000},
                                                 "aggs": {"the_sum": {"sum": {"field": order_fields[n]}},
                                                          "citation_bucket_sort": {
                                                              "bucket_sort": {"sort": [{"the_sum": {"order": "desc"}}],
                                                                              "size": num}}}}}})
        a = res['aggregations']['names']['buckets']
        for i in a:
            result_lst.append({"name": i["key"], "papers": i["doc_count"], "citations": i["the_sum"]["value"]})
        result = {"lst": result_lst, 'result': 'ok'}

    # elenca i primi x per numero di pubblicazioni ultimi 5 anni con x != papers e istanza di tipo obj qualsiasi
    # tranne il caso in cui sub=autore e obj=organizzazione
    elif sub != '2' and ins != 'all' and order == '3' and not (sub == '1' and obj == '3'):
        year = datetime.datetime.now().year
        res = es.search(index=index, body={"size": 0, "track_total_hits": 'true', "query": {
            "bool": {"must": [{"range": {"year": {"gte": year - 5, "lte": year}}},
                              {"match_phrase": {obj_field: ins}}]}},
                                           "aggs": {"names": {"terms": {"field": sub_field, "size": num}}}})
        a = res['aggregations']['names']['buckets']
        for i in a:
            result_lst.append({"name": i["key"], "papers": i["doc_count"]})
        result = {"lst": result_lst, 'result': 'ok'}

    # elenca i primi x per numero di citazioni(entrambi i casi) con x = papers e nessuna istanza
    elif sub == '2' and ins == 'all' and (order == '2' or order == '4'):
        n = int(int(order) / 2 - 1)
        res = es.search(index=index, body={"track_total_hits": 'true', "size": num,
                                           "_source": ["papertitle", order_fields[n], "authors"],
                                           "query": {"match_all": {}}, "sort": [{order_fields[n]: {"order": "desc"}}]})
        a = res['hits']['hits']
        for i in a:
            author = authors_name(i['_source']['authors'])
            result_lst.append(
                {"name": i['_source']["papertitle"], "citations": i['_source'][order_fields[n]], "author": author})
        result = {"lst": result_lst, 'result': 'ok'}

    # elenca i primi x per numero di citazioni(entrambi i casi) con x = papers e istanza qualsiasi
    elif sub == '2' and ins != 'all' and (order == '2' or order == '4'):
        n = int(int(order) / 2 - 1)
        res = es.search(index=index, body={"track_total_hits": 'true', "size": num,
                                           "_source": ["papertitle", order_fields[n], "authors"],
                                           "query": {"match_phrase": {obj_field: ins}},
                                           "sort": [{order_fields[n]: {"order": "desc"}}]})
        a = res['hits']['hits']
        for i in a:
            author = ''
            if obj != '4':
                author = authors_name(i['_source']['authors'])
            result_lst.append(
                {"name": i['_source']["papertitle"], "citations": i['_source'][order_fields[n]], "author": author})
        result = {"lst": result_lst, 'result': 'ok'}

    # elenca i primi x per numero di pubblicazioni con x = autori e istanza di tipo organizzazione
    elif sub == '1' and obj == '3' and ins != 'all' and order == '1':
        res = es.search(index=index,
                        body={"size": 0, "track_total_hits": 'true', "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"names": {"terms": {"field": sub_field, "size": num * 5}}}})
        a = res['aggregations']['names']['buckets']
        for i in a:            
            res1 = es.search(index=author_index, body = {"size": 1,"track_total_hits": 'true', "query": {"bool": {"must": [{"match_phrase": {"id": i["key"]}},{"match_phrase": {"affiliation": ins}}]}}})
            
            if res1['hits']['total']['value'] > 0:
                author_name = res1['hits']['hits'][0]['_source'].get('name')
                result_lst.append({"name": author_name, "papers": i["doc_count"]})
            if len(result_lst) >= num:
                break
        result = {"lst": result_lst, 'result': 'ok'}
        return json.dumps(result)

    # elenca i primi x per numero di citazioni (entrambi i casi) con x = autori e istanza di tipo organizzazione
    elif sub == '1' and obj == '3' and ins != 'all' and (order == '2' or order == '4'):
        n = int(int(order) / 2 - 1)
        res = es.search(index=index,
                        body={"size": 0, "track_total_hits": 'true', "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"names": {"terms": {"field": sub_field, "size": 50000},
                                                 "aggs": {"the_sum": {"sum": {"field": order_fields[n]}},
                                                          "citation_bucket_sort": {
                                                              "bucket_sort": {"sort": [{"the_sum": {"order": "desc"}}],
                                                                              "size": num * 5}}}}}})
        a = res['aggregations']['names']['buckets']
        print('risultati ',a)
       
        
        for i in a:
            res1 = es.search(index=author_index, body = {"size": 1,"track_total_hits": 'true', "query": {"bool": {"must": [{"match_phrase": {"id": i["key"]}},{"match_phrase": {"affiliation": ins}}]}}})

            if res1['hits']['total']['value'] > 0: 
                author_name = res1['hits']['hits'][0]['_source'].get('name')
                result_lst.append({"name": author_name, "papers": i["doc_count"], "citations": i["the_sum"]["value"]})
            if len(result_lst) >= num:
                break
        result = {"lst": result_lst, 'result': 'ok'}
        return json.dumps(result)

    # elenca i primi x per numero di pubblicazioni ultimi 5 anni con x = autori e istanza di tipo organizzazione
    elif sub == '1' and obj == '3' and ins != 'all' and order == '3':
        year = datetime.datetime.now().year
        res = es.search(index=index, body={"size": 0, "track_total_hits": 'true',
                                           "query": {
                                               "bool": {"must": [{"range": {"year": {"gte": year - 5, "lte": year}}},
                                                                 {"match_phrase": {obj_field: ins}}]}},
                                           "aggs": {"names": {"terms": {"field": sub_field, "size": num * 5}}}})
        a = res['aggregations']['names']['buckets']
        for i in a:
            res1 = es.search(index=author_index, body = {"size": 1,"track_total_hits": 'true', "query": {"bool": {"must": [{"match_phrase": {"id": i["key"]}},{"match_phrase": {"affiliation": ins}}]}}})
            if res1['hits']['total']['value'] > 0:
                author_name = res1['hits']['hits'][0]['_source'].get('name')
                result_lst.append({"name": author_name, "papers": i["doc_count"]})
            if len(result_lst) >= num:
                break
        result = {"lst": result_lst, 'result': 'ok'}
        return json.dumps(result)

    if sub == '1' or sub == '3':
        item_lst = []
        for item in result['lst']:
            if type(item['name']) is int:
                if sub == '1':
                    res1 = es.search(index=author_index, body={"size": 1, "track_total_hits": 'true',
                                                               "query": {"match_phrase": {'id': item['name']}}})
                    author_name = res1['hits']['hits'][0]['_source'].get('name')
                    item['name'] = author_name
                    item_lst.append(item)
                if sub == '3':
                    res1 = es.search(index=dsc_conferences_index, body={"size": 1, "track_total_hits": 'true',
                                                                        "query": {
                                                                            "match_phrase": {'id': item['name']}}})
                    conf_name = res1['hits']['hits'][0]['_source'].get('name') + ' (' + res1['hits']['hits'][0][
                        '_source'].get('acronym') + ')'
                    item['name'] = conf_name
                    item_lst.append(item)
        result['lst'] = item_lst

    return json.dumps(result)


def how(sub, obj, ins):
    sub_fields = ['authors.id', '', 'conferenceseriesid', 'authors.affiliation.keyword', 'citationcount']
    obj_fields = ['cso_enhanced_topics.keyword', 'conferenceseriesid', 'authors.affiliation.keyword', 'authors.id']
    sub_field = sub_fields[int(sub) - 1]
    obj_field = 0
    if 0 < int(obj) < 5:
        obj_field = obj_fields[int(obj) - 1]
    result = json.dumps({'result': 'Query not implemented yet'})

    if sub == '1' and obj == '1' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '1' and obj == '2' and ins == 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"exists": {"field": obj_field}},
                              "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '1' and obj == '2' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '1' and obj == '3' and ins != 'no':
        res = es.search(index=author_index, body={"track_total_hits": 'true', "size": 0,
                                                  "query": {"match_phrase": {"affiliation.keyword": ins}},
                                                  "aggs": {"A": {"cardinality": {"field": "id"}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '1' and obj == '5' and ins == 'no':
        res = es.search(index=index, body={"track_total_hits": 'true', "size": 0, "query": {"match_all": {}},
                                           "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})

    elif sub == '2' and obj == '1' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}}})
        message = str(res['hits']['total']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '2' and obj == '2' and ins == 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"exists": {"field": obj_field}}})
        message = str(res['hits']['total']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '2' and obj == '2' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}}})
        message = str(res['hits']['total']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '2' and obj == '3' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}}})
        message = str(res['hits']['total']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '2' and obj == '4' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}}})
        message = str(res['hits']['total']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '2' and obj == '5' and ins == 'no':
        res = es.search(index=index, body={"track_total_hits": 'true', "size": 0, "query": {"match_all": {}}})
        message = str(res['hits']['total']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})

    elif sub == '3' and obj == '1' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '3' and obj == '2' and ins == 'no':
        res = es.search(index=dsc_conferences_index,
                        body={"size": 0, "track_total_hits": "true", "query": {"match_all": {}}})
        message = str(res['hits']['total']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '3' and obj == '3' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '3' and obj == '4' and ins != 'no':
        res = es.search(index=index, body={"size": 0, "track_total_hits": "true", "query": {
            "bool": {"must": [{"exists": {"field": sub_field}}, {"match_phrase": {obj_field: ins}}]}},
                                           "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(int(res['aggregations']['A']['value']))
        result = json.dumps({'hits': message, 'result': 'ok'})

    elif sub == '4' and obj == '1' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '4' and obj == '2' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"A": {"cardinality": {"field": sub_field}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '4' and obj == '3' and ins == 'no':
        res = es.search(index=author_index, body={"track_total_hits": 'true', "size": 0, "query": {"match_all": {}},
                                                  "aggs": {"A": {"cardinality": {"field": "affiliation.keyword"}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '4' and obj == '4' and ins != 'no':
        res = es.search(index=author_index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {"id": ins}},
                              "aggs": {"A": {"cardinality": {"field": "affiliation.keyword"}}}})
        message = str(res['aggregations']['A']['value'])
        result = json.dumps({'hits': message, 'result': 'ok'})

    elif sub == '5' and obj == '1' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"Sum": {"sum": {"field": sub_field}}}})
        message = str(int(res['aggregations']['Sum']['value']))
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '5' and obj == '2' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"Sum": {"sum": {"field": sub_field}}}})
        message = str(int(res['aggregations']['Sum']['value']))
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '5' and obj == '3' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"Sum": {"sum": {"field": sub_field}}}})
        message = str(int(res['aggregations']['Sum']['value']))
        result = json.dumps({'hits': message, 'result': 'ok'})
    elif sub == '5' and obj == '4' and ins != 'no':
        res = es.search(index=index,
                        body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {obj_field: ins}},
                              "aggs": {"Sum": {"sum": {"field": sub_field}}}})
        message = str(int(res['aggregations']['Sum']['value']))
        result = json.dumps({'hits': message, 'result': 'ok'})

    return result


# finds correspondence between the parameter and one of the database fields in the fields list
def find_match(ins):
    fields = ["cso_enhanced_topics", "confseries", "affiliation", "name"]
    es_index = [index, index, author_index, author_index]
    objects = ["topics", "conferences", "organizations", "authors"]

    obj_id = 0
    res0 = []
    res1 = []
    res2 = []
    res3 = []
    found_hits = []
    found_keys = []
    found_keywords = []
    cat_found = 0
    keywords_found = 0
    keys = [[], [], [], []]
    keys2 = [[], [], [], []]

    # ricerca per chiave esatta
    for i in range(4):
        res0.append(es.search(index=es_index[i], body={"track_total_hits": 'true', "size": 0,
                                                       "query": {"match_phrase": {fields[i] + ".keyword": ins}},
                                                       "aggs": {
                                                           "A": {"cardinality": {"field": fields[i] + ".keyword"}}}}))
        found_keywords.append(res0[i]['aggregations']['A']['value'])

        if found_keywords[i] > 0:
            keywords_found = keywords_found + 1

    if keywords_found == 1:
        obj_id = found_keywords.index(max(found_keywords))
        return json.dumps({'result': 'ok', 'object': objects[obj_id], 'obj_id': obj_id + 1, 'item': ins})

    # ricerca per frase
    for i in range(4):
        res1.append(es.search(index=es_index[i],
                              body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {fields[i]: ins}},
                                    "aggs": {"A": {"cardinality": {"field": fields[i] + ".keyword"}}}}))
        res2.append(es.search(index=es_index[i],
                              body={"track_total_hits": 'true', "size": 0, "query": {"match_phrase": {fields[i]: ins}},
                                    "aggs": {"A": {"terms": {"field": fields[i] + ".keyword", "size": 100}}}}))
        res3.append(es.search(index=es_index[obj_id], body={"track_total_hits": 'true', "size": 0, "query": {
            "match_phrase": {fields[obj_id] + ".keyword": ins.lower()}}, "aggs": {
            "A": {"cardinality": {"field": fields[obj_id] + ".keyword"}}}}))
        found_hits.append(res1[i]['aggregations']['A']['value'])
        found_keys.append(res3[i]['aggregations']['A']['value'])

        if found_hits[i] > 0:
            cat_found = cat_found + 1
            for j in res2[i]['aggregations']['A']['buckets']:
                keys2[i].append(j['key'].lower())
                keys[i].append(j['key'])

    # risolve il problema che es non restituisce i singoli valori dei topics nelle aggregazioni
    # perchè sono contenuti in un array
    keys[0] = [s for s in keys[0] if ins.lower() in s]
    keys2[0] = keys[0]

    found_hits[0] = len(keys[0])
    obj_id = found_hits.index(max(found_hits))
    for i in range(4):
        keys[i] = keys[i][:3]
        keys2[i] = keys2[i][:3]

    # caso con più di tre risultati in una categoria
    if max(found_hits) > 3 and cat_found > 1:
        return json.dumps({'result': 'kk', 'num': found_hits})

    # caso con 3 o meno risultati in più di una categoria
    if cat_found > 1:
        return json.dumps({'result': 'k2', 'num': found_hits, 'keys': keys})

    # caso con 1 risultato utile
    num = found_hits[obj_id]
    num2 = found_keys[obj_id]

    if num == 1 or num2 == 1 or (ins.lower() in keys2[obj_id]):
        if ins.lower() in keys2[obj_id]:
            item = keys[obj_id][keys2[obj_id].index(ins.lower())]
        else:
            item = keys[obj_id][0]
        # print({'object': objects[obj_id], 'result': 'ok', 'obj_id': obj_id + 1, 'item': item})
        return json.dumps({'result': 'ok', 'object': objects[obj_id], 'obj_id': obj_id + 1, 'item': item})

    # caso con più di tre risultati in una sola categoria
    elif num > 3 or sum(found_hits)>10:
        return json.dumps({'result': 'kk', 'num': found_hits})

    # ricerca fuzzy
    res0 = []
    found = [[], [], [], []]
    keys = [[], [], [], []]
    source = ["cso_enhanced_topics", "confseries", "affiliation", ["name", "affiliation"]]

    # ricerca in es come per la ricerca esatta ma con il parametro fuzziness e con match al posto di match_phrase
    for i in range(4):
        res0.append(es.search(index=es_index[i], body={"size": 10, "track_total_hits": "true", "_source": source[i],
                                                       "query": {"match": {
                                                           fields[i]: {"query": ins, "fuzziness": "auto",
                                                                       "max_expansions": 50, "prefix_length": 0}}}}))

        # elimina i doppioni
        voice = []
        for data in res0[i]['hits']['hits']:
            if data['_source'][fields[i]] not in voice:
                voice.append(data['_source'][fields[i]])
                found[i].append(data['_source'][fields[i]])

    # genera una lista per i topic a partire dalle liste recuperate nei 10 documenti da es, eliminando i doppioni
    flat = []
    flat_list = [item for topic in found[0] for item in topic]
    for element in flat_list:
        if element not in flat:
            flat.append(element)
    found[0] = flat

    # estrae i valori più probabili e calcola il punteggio: se ci sono valori sopra soglia
    # li salva nella lista delle chiavi più probabili
    for i in range(4):
        found[i] = process.extract(ins, found[i], limit=3)
        for data in found[i]:
            if data[1] > threshold:
                keys[i].append(data[0])

    # prende solo i primi tre valori per ogni campo e verifica se siamo in presenza
    # di un unico valore candidato e in tal caso lo restituisce
    keys = [keys[0][:3], keys[1][:3], keys[2][:3], keys[3][:3]]
    num = [len(a) for a in keys]
    if sum(num) == 1:
        obj_id = num.index(1)
        item = keys[obj_id][0]
        return json.dumps({'result': 'ok', 'object': objects[obj_id], 'obj_id': obj_id + 1, 'item': item})

    for i in range(4):
        flat = []
        for data in found[i]:
            if data[1] > (threshold - 15):
                flat.append(data[0])
            found[i] = flat[:3]

    num = [len(a) for a in found]

    # print(num)
    # print(found)

    if sum(num) == 1:
        obj_id = num.index(1)
        item = found[obj_id][0]
        return json.dumps({'result': 'ok', 'object': objects[obj_id], 'obj_id': obj_id + 1, 'item': item})

    if sum(num) > 1 and sum(num) < 11:
        return json.dumps({'result': 'k2', 'num': num, 'keys': found})

    if sum(num) > 10:
        return json.dumps({'result': 'kk', 'num': num})

    # nessun risultato
    return json.dumps({'result': 'ko', 'object': '', 'obj_id': 0, 'keys': [], 'num': 0})


# disambiguazione conferenze omonime per ricerca fnd
def check_conference(result):
    res = es.search(index=dsc_conferences_index,
                    body={"track_total_hits": "true", "query": {"match_phrase": {"acronym": result['item']}}})
    hits = res['hits']['total']['value']
    if hits == 1:
        conference_id = res['hits']['hits'][0]['_source']['id']
        result['id'] = conference_id
    elif hits > 1:
        conferences = []
        for conf in res['hits']['hits']:
            conferences.append(
                {'name': conf['_source']['name'], 'acronym': conf['_source']['acronym'], 'id': conf['_source']['id']})
        result['result'] = 'ka'
        result['item'] = conferences
    elif hits < 1:
        result['result'] = 'ko'
        
    return json.dumps(result)


# disambiguazione autori omonimi per ricerca fnd
def check_author(result):
    res = es.search(index=author_index,
                    body={"track_total_hits": "true", "query": {"match_phrase": {"name.keyword": result['item']}},
                          "aggs": {"a": {"terms": {"field": "id", "size": 10}}}})
    hits = res['hits']['total']['value']
    unique_id_num = len(res['aggregations']['a']['buckets'])
    if hits == 1 or unique_id_num == 1:
        author_id = res['hits']['hits'][0]['_source']['id']
        result['id'] = author_id
    else:
        authors = []
        authors2 = []
        affiliations = []
        paper = ''

        for author in res['hits']['hits']:
            res_author = es.search(index=index,
                                   body={"track_total_hits": "true", "sort": [{"citationcount": {"order": "desc"}}],
                                         "query": {"match_phrase": {"authors.id": author['_source']['id']}}})
            author_publications = res_author['hits']['total']['value']
            if author_publications > 0:
                paper = res_author['hits']['hits'][0]['_source']['papertitle']
            if 'affiliation' in author['_source']:
                if author['_source'].get('affiliation') in affiliations:
                    aut_ind = affiliations.index(author['_source'].get('affiliation'))
                    if author_publications > authors[aut_ind]['publications']:
                        authors[aut_ind] = {'name': author['_source']['name'], 'id': author['_source']['id'],
                                            'affiliation': author['_source']['affiliation'],
                                            'publications': author_publications,
                                            'paper': paper}
                else:
                    affiliations.append(author['_source'].get('affiliation'))
                    authors.append({'name': author['_source']['name'], 'id': author['_source']['id'],
                                    'affiliation': author['_source']['affiliation'],
                                    'publications': author_publications,
                                    'paper': paper})
            else:
                authors2.append({'name': author['_source']['name'], 'id': author['_source']['id'],
                                 'publications': author_publications, 'paper': paper})

        if len(authors) > 1:
            result['result'] = 'ka'
            result['item'] = authors
        elif len(authors) == 1:
            result['author_id'] = authors[0]['id']
        else:
            result['result'] = 'ka'
            result['item'] = authors2

    return json.dumps(result)


# disambiguazione autori omonimi per ricerca dsc
def dsc_check_author(query):
    authors = []
    authors2 = []
    affiliations = []
    res = es.search(index=dsc_authors_index,
                    body={"size": 100, "track_total_hits": "true", "sort": [{"publications": {"order": "desc"}}],
                          "query": {"match_phrase": {"name": query}}})

    for author in res['hits']['hits']:
        author_publications = author['_source'].get('publications')
        if 'last_affiliation' in author['_source'] and 'affiliation_name' in author['_source']['last_affiliation']:
            affiliation = author['_source']['last_affiliation']
            if affiliation.get('affiliation_name') in affiliations:
                aut_ind = affiliations.index(affiliation.get('affiliation_name'))
                if author_publications > authors[aut_ind]['publications']:
                    authors[aut_ind] = {'name': author['_source']['name'], 'id': author['_source']['id'],
                                        'affiliation': affiliation.get('affiliation_name'),
                                        'publications': author_publications}
            else:
                affiliations.append(affiliation.get('affiliation_name'))
                authors.append({'name': author['_source']['name'], 'id': author['_source']['id'],
                                'affiliation': affiliation.get('affiliation_name'),
                                'publications': author_publications})
        else:
            authors2.append({'name': author['_source']['name'], 'id': author['_source']['id'],
                             'publications': author_publications})
    authors.extend(authors2)
    if len(authors) == 1:
        for author in res['hits']['hits']:
            if author['_source']['id'] == authors[0]['id']:
                return [author['_source']]
    return authors[:9]


def author_data(author_id):
    blacklist = ['lecture notes in computer science', 'arxiv software engineering']
    top_pub_conf = []
    top_cit_conf = []

    res1 = es.search(index=index,
                     body={"size": 0, "track_total_hits": "true", "query": {"match_phrase": {"authors.id": author_id}},
                           "aggs": {"a": {"cardinality": {"field": "authors.id"}}}})
    res2 = es.search(index=index,
                     body={"size": 0, "track_total_hits": "true", "query": {"match_phrase": {"authors.id": author_id}},
                           "aggs": {"a": {"terms": {"field": "confseries.keyword", "size": 3}}}})
    res3 = es.search(index=index,
                     body={"size": 0, "track_total_hits": "true", "query": {"match_phrase": {"authors.id": author_id}},
                           "aggs": {"a": {"terms": {"field": "confseries.keyword"},
                                          "aggs": {"the_sum": {"sum": {"field": "citationcount"}},
                                                   "citation_bucket_sort": {
                                                       "bucket_sort": {"sort": [{"the_sum": {"order": "desc"}}],
                                                                       "size": 3}}}}}})
    res4 = es.search(index=index,
                     body={"size": 0, "track_total_hits": "true", "query": {"match_phrase": {"authors.id": author_id}},
                           "aggs": {"a": {"terms": {"field": "journame.keyword", "size": 3 + len(blacklist)}}}})

    co_authors = res1['aggregations']['a']['value'] - 1
    top_journals = []
    for journal in res4['aggregations']['a']['buckets']:
        first = journal['key'].split(' ')[0]
        if journal['key'] not in blacklist and first != 'arxiv':
            top_journals.append({'name': journal['key'], 'publications': journal['doc_count']})

    if co_authors < 0:
        co_authors = 0
    top_pub = res2['aggregations']['a']['buckets']
    top_cit = res3['aggregations']['a']['buckets']
    for conf in top_pub:
        top_pub_conf.append({'name': conf['key'], 'publications': conf['doc_count']})
    for conf in top_cit:
        top_cit_conf.append({'name': conf['key'], 'citations': int(conf['the_sum']['value'])})
    return {'co_authors': co_authors, 'top_pub_conf': top_pub_conf, 'top_cit_conf': top_cit_conf,
            'top_journals': top_journals[:3]}


def dsc_finder(query):
    dsc_indexes = [dsc_authors_index, dsc_conferences_index, dsc_conferences_index]
    dsc_exact_fields = ['name.keyword', 'acronym', 'name.keyword']
    dsc_fields = ['name', 'acronym', 'name']
    objects = ['authors', 'conferences', 'conferences']
    res = []
    num = []
    keys = [[], [], []]
    result = {'result': 'ko'}

    # ricerca esatta per id
    if query.isnumeric():
        res = es.search(index=dsc_authors_index,
                        body={"track_total_hits": "true", "query": {"match_phrase": {'id': query}}})
        if res['hits']['total']['value'] == 1:
            result = ({'result': 'ok', 'obj_id': 1, 'object': objects[1],
                       'item': res['hits']['hits'][0]['_source'] | author_data(
                           res['hits']['hits'][0]['_source']['id'])})
        return json.dumps(result)

    # ricerca esatta
    for i in range(len(dsc_indexes)):
        res.append(es.search(index=dsc_indexes[i], body={"track_total_hits": "true", "query": {
            "match_phrase": {dsc_exact_fields[i]: query.lower()}}}))
        num.append(res[i]['hits']['total']['value'])

    obj_id = num.index(max(num))
    if sum(num) == 1:
        result = ({'result': 'ok', 'obj_id': obj_id + 1, 'object': objects[obj_id],
                   'item': res[obj_id]['hits']['hits'][0]['_source']})
        if obj_id == 0:
            # noinspection PyTypeChecker
            result['item'] = (result['item'] | author_data(res[obj_id]['hits']['hits'][0]['_source']['id']))
        return json.dumps(result)
    elif sum(num) > 1 and obj_id == 0:
        auth_list = dsc_check_author(query)
        # print(len(auth_list))
        if len(auth_list) > 1:
            result = {'result': 'ka', 'obj_id': obj_id + 1, 'object': objects[obj_id], 'item': auth_list}
        else:
            result = ({'result': 'ok', 'obj_id': obj_id + 1, 'object': objects[obj_id],
                       'item': auth_list[0] | author_data(auth_list[0]['id'])})
        return json.dumps(result)

    # ricerca per frase
    res = []
    num = []
    for i in range(len(dsc_indexes)):
        res.append(es.search(index=dsc_indexes[i],
                             body={"track_total_hits": "true", "query": {"match_phrase": {dsc_fields[i]: query}}}))
        num.append(res[i]['hits']['total']['value'])
    # print(num)
    obj_id = num.index(max(num))
    if sum(num) == 1:
        result = ({'result': 'ok', 'obj_id': obj_id + 1, 'object': objects[obj_id],
                   'item': res[obj_id]['hits']['hits'][0]['_source']})
        if obj_id == 0:
            # noinspection PyTypeChecker
            result['item'] = result['item'] | author_data(res[obj_id]['hits']['hits'][0]['_source']['id'])
        return json.dumps(result)

    if 1 < max(num) <= 6:
        names = ['last affiliation', 'acronym', 'acronym']
        for i in range(len(dsc_indexes)):
            for data in res[i]['hits']['hits']:
                item = data['_source']
                key = {'id': item['id'], 'name': item['name']}
                if names[i] in item:
                    key[names[i]] = item[names[i]]
                keys[i].append(key)
        result = {'result': 'k2', 'num': num, 'keys': keys}
        # print(result)

    if max(num) > 3 or sum(num) > 10:
        result = {'result': 'kk', 'num': num}

    return json.dumps(result)
