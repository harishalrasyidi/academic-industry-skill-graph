# Demo SPARQL Queries

Gunakan query berikut pada halaman `/query` setelah ontology OBC di-upload ke dataset Fuseki.

## 1. Daftar Mata Kuliah

```sparql
PREFIX obc: <http://www.semanticweb.org/ami/ontologies/2024/0/OBC#>

SELECT ?course ?courseName ?credit ?semester
WHERE {
  ?course a obc:Course ;
          obc:courseName ?courseName .

  OPTIONAL { ?course obc:credit ?credit }
  OPTIONAL { ?course obc:semester ?semester }
}
ORDER BY ?courseName
LIMIT 20
```

Query ini menampilkan hingga 20 mata kuliah beserta nama, jumlah kredit, dan semester jika tersedia.

## 2. PLO dan Mata Kuliah Terkait

```sparql
PREFIX obc: <http://www.semanticweb.org/ami/ontologies/2024/0/OBC#>

SELECT ?plo ?ploLabel ?course ?courseName
WHERE {
  ?plo a obc:ProgramLearningOutcome ;
       obc:label ?ploLabel ;
       obc:ploHasCourse ?course .

  OPTIONAL {
    ?course obc:courseName ?courseName
  }
}
ORDER BY ?ploLabel
LIMIT 30
```

Query ini memperlihatkan hubungan antara Program Learning Outcome dan mata kuliah yang mendukungnya.

## 3. Course Learning Outcome

```sparql
PREFIX obc: <http://www.semanticweb.org/ami/ontologies/2024/0/OBC#>

SELECT ?clo ?label ?description ?domain
WHERE {
  ?clo a obc:CourseLearningOutcome .

  OPTIONAL { ?clo obc:label ?label }
  OPTIONAL { ?clo obc:description ?description }
  OPTIONAL { ?clo obc:hasDomain ?domain }
}
ORDER BY ?label
LIMIT 20
```

Query ini menampilkan Course Learning Outcome beserta label, deskripsi, dan domain pembelajarannya.

## 4. Instance AffectiveDomain

```sparql
PREFIX obc: <http://www.semanticweb.org/ami/ontologies/2024/0/OBC#>

SELECT ?instance ?label
WHERE {
  ?instance a obc:AffectiveDomain .

  OPTIONAL {
    ?instance obc:label ?label
  }
}
ORDER BY ?label
```

Query ini menampilkan semua instance yang termasuk dalam kelas `AffectiveDomain`, seperti `A1_Perceive` dan `A2_React`.

## 5. Link ke Wikidata

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?entity ?wikidata
WHERE {
  ?entity owl:sameAs ?wikidata .

  FILTER(CONTAINS(STR(?wikidata), "wikidata.org/entity"))
}
```

Query ini mencari semua entity yang memiliki hubungan `owl:sameAs` dengan entity di Wikidata.

## 6. Metadata Property

```sparql
PREFIX obc: <http://www.semanticweb.org/ami/ontologies/2024/0/OBC#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?type ?domain ?range
WHERE {
  VALUES ?property {
    obc:courseName
    obc:credit
    obc:semester
    obc:hasPLO
  }

  OPTIONAL { ?property a ?type }
  OPTIONAL { ?property rdfs:domain ?domain }
  OPTIONAL { ?property rdfs:range ?range }
}
```

Query ini menampilkan tipe, domain, dan range dari beberapa property utama pada ontology OBC.

## 7. Semua Triple untuk Menguji Navigasi

```sparql
SELECT ?subject ?predicate ?object
WHERE {
  ?subject ?predicate ?object .
}
LIMIT 20
```

Query ini cocok untuk menguji navigasi karena subject dan predicate URI dapat diklik menuju screen entity atau property.
