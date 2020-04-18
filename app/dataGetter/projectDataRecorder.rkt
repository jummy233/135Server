#lang racket
(require typed/racket
         (only-in gregor datetime datetime->iso8601)
         data/maybe
         json
         racket/trace)

(define data-folder-path "../../../doc/shisanwu_txt/")
(define spliter "«")
(define empty-box "□")

(struct Project
  ([project-name : String]            ;
   [outdoor-spot : String]            ; FK
   [location : String]                ; FK
   [construction-company : String]
   [tech_support-company : String]
   [project-company : String]
   [floor : String]
   [latitude : String]
   [longitude : String]
   [district : String]
   [area : String]
   [demo-area : String]
   [building-type : String]
   [building-height : String]

   [started-time : String]
   [finished-time : String]
   [record-started-from : String]
   [description : String]))

(define (mk-project
    #:project-name [project-name ""]           ;
    #:outdoor-spot [outdoor-spot ""]           ; FK
    #:location [location ""]                   ; FK
    #:construction-company [construction-company ""]
    #:tech_support-company [tech_support-company ""]
    #:project-company [project-company ""]
    #:floor [floor ""]
    #:latitude [latitude ""]
    #:longitude [longitude ""]
    #:district [district ""]
    #:area [area ""]
    #:demo-area [demo-area ""]
    #:building-type [building-type ""]
    #:building-height [building-height ""]
    #:started-time [started-time ""]
    #:finished-time [finished-time ""]
    #:record-started_from [record-started-from ""]
    #:description [description ""])
  (Project project-name outdoor-spot location construction-company tech_support-company
           project-company floor latitude longitude district area demo-area building-type
           building-height started-time finished-time record-started-from description))

(define (docs-data->list str) (regexp-split "\n\n" str))
(define (insert-line str key)
  (match-let
    ([(list a b)
      (regexp-split key str)])
    (string-append a "\n" key b)))
(define (split-to-cdr keys str)
  (match-let
    ([(list a b) (regexp-split keys str)])
    (list a (string-append keys spliter b))))

(: crop-proj-info (-> str (Listof String)))
(define (crop-proj-info str)
  (let*
    ([special-case-list
       (list
         "数据监测信息"
         "建筑楼层数"
         "示范面积（㎡）"
         "竣工时间"
         "开始监测时间")]
     [splited (letrec
                ([rec (λ (str keys)
                        (if (null? keys)
                          str (rec (insert-line str (car keys)) (cdr keys))))])
                (rec str special-case-list))]
     [proj-info (list-ref (regexp-split "其他:" splited) 0)])
    (match-let*
      ([(list a b)
        (split-to-cdr "示范工程技术亮点" proj-info)]
       [lista
         (map (curry regexp-split "\n") (docs-data->list a))]
       [listb
         (list (regexp-split spliter b))])
      (append lista listb))))

(define-type Parser (-> Parser (Listof String) (Maybe String)))

(: parse (-> Parser (Listof String) (Maybe Any)))
(define (parse token proj parser)
  (let ([result (parser token proj)])
    (if (just? result)
      result
      nothing)))

#| ----------------------- |#
#| -  parser combinator  - |#
#| ----------------------- |#
(define (alt parsers)
  (λ (token proj)
     (let ([reslist (filter just? (map (curry parse token proj) parsers))])
       (if (null? reslist) proj  ; if no result return the same proj
         (from-just proj (first reslist))))))


(define (parse-projectname token proj)  ; Just Project
  (if (member "示范工程名称" token)
    (just (curry
            proj
            #:project-name (list-ref token 3)))
    nothing))

(define (parse-location token proj)
  (if (member "示范工程地址" token)
    (just (curry
            proj
            #:location (list-ref token 1)))
    nothing))

(define (parse-construction-company token proj)
  (if (member "建设单位" token)
    (just (curry
            proj
            #:construction-company (list-ref token 1)))
    nothing))

(define (parse-tech-support-company token proj)
  (if (member "技术支撑单位" token)
    (just (curry
            proj
            #:tech_support-company (list-ref token 1)))
    nothing))

(define (parse-project-company token proj)
  (if (member "负责单位" token)
    (just (curry
            proj
            #:project-company (list-ref token 1)))
    nothing))

(define (parse-floor token proj)
  (if (member "建筑楼层数" token)
    (just (curry
            proj
            #:floor (list-ref token 1)))
    nothing))

(define (parse-demo-area  token proj)
  (if (member "示范面积（㎡）" token)
    (just (curry
            proj
            #:demo-area (list-ref token 1)))
    nothing))

(define (parse-area token proj)
  (if (member "建筑面积（㎡）" token)
    (just (curry
            proj
            #:area (list-ref token 1)))
    nothing))

(define (parse-building_type token proj)
  (if (member "示范工程类型" token)
    (just (curry
            proj #:building-type
            (letrec
              ([type (λ (entry)
                        (if (null? entry)
                          ""
                          (match-let
                            ([(list a b) (regexp-split " " (car entry))])
                            (if (not (equal? a empty-box))
                              b (type (cdr entry))))))])
                   (type (cdr token)))))
    nothing))

(define (parse-building_height token proj)
  (if (member "建筑高度" token)
    (just (curry
            proj
            #:building-height (list-ref token 1)))
    nothing))


(: parse-datetime (-> String -> String))
(define (parse-datetime datestring)
  (if (or (equal? "" datestring) (equal? "/" datestring))
    ""
    (datetime->iso8601
      (apply datetime (map string->number (regexp-split "\\.|-|[日|月]" datestring))))))

(define (parse-started-time token proj)
  (if (member "开工时间" token)
    (just (curry
            proj
            #:started-time (parse-datetime (list-ref token 2))))
    nothing))

(define (parse-finished-time token proj)
  (if (member "竣工时间" token)
    (just (curry
            proj
            #:finished-time (parse-datetime (list-ref token 1))))
    nothing))

(define (parse-record-started_from token proj)
  (if (member "开始监测时间" token)
    (just (curry
            proj
            #:record-started_from (parse-datetime (list-ref token 1))))
    nothing))

(define (parse-description token proj)
  (if (member "示范工程技术亮点" token)
    (just (curry
            proj
            #:description (list-ref token 1)))
    nothing))


; alt parser
(: parser (-> String (-> Any Project) (Maybe (-> Any Project))))
(define parser
  (alt (list
         parse-projectname
         parse-location
         parse-construction-company
         parse-tech-support-company
         parse-project-company
         parse-floor
         parse-demo-area
         parse-area
         parse-building_height
         parse-building_type
         parse-started-time
         parse-finished-time
         parse-record-started_from
         parse-description)))

(define (parse-all data proj)
  (let
    ([newproj (parser (car data) proj)])
    (if (null? (cdr data))
      (proj)
      (parse-all (cdr data) newproj))))

(define (parse-project data) (parse-all data mk-project))

#| (pretty-print (parse-all data mk-project)) |#

#| ---------------- |#
#| -  Run script  - |#
#| ---------------- |#

(define filenames
  (for/list ([i (in-range 1 31)]) (string-append "a" (number->string i) ".txt")))

(define (concat-path path filename) (string-append path filename))

(define (get-data path) (crop-proj-info (file->string path)))


#| ---------- |#
#| -  Json  - |#
#| ---------- |#


(define (project-to-hash proj) ; proj: Project struct.
    (hash 'project_name (Project-project-name proj)
          'location (Project-location proj)
          'outdoor_spot (Project-outdoor-spot proj)
          'construction_company (Project-construction-company proj)
          'tech_support_company (Project-tech_support-company proj)
          'project_company (Project-project-company proj)
          'floor (Project-floor proj)
          'latitude (Project-latitude proj)
          'longitude (Project-longitude proj)
          'district (Project-district proj)
          'area (Project-area proj)
          'demo_area (Project-demo-area proj)
          'building_type (Project-building-type proj)
          'building_height (Project-building-height proj)
          'started_time (Project-started-time proj)
          'finished_time (Project-finished-time proj)
          'record_started_from (Project-record-started-from proj)
          'description (Project-description proj)))

(define (proj-to-json out proj-hash) (write-json out proj-hash))

; DEBUG
#| (print (project-to-hash (parse-project data1))) |#

; file context
(define (with-out-append file-path fn)
  (let ([out (open-output-file file-path #:exists 'append)])
    (fn out)
    (close-output-port out)))

(define (with-in-read file-path fn)
  (let ([in (open-input-file file-path)])
    (fn in)
    (close-input-port in)))

; combined project
(define (combine-projects)  ; hash of all projects.
  (let* ([mk-hdata (lambda (in-path)
                     (let ([data (get-data in-path)])
                       (project-to-hash (parse-project data))))]
         [in-path-list (map (curry concat-path data-folder-path) filenames)]
         [projects-hash (hash 'data (map mk-hdata in-path-list))])
    projects-hash))

(with-out-append
  (concat-path "./static/" "projects.json")
  (lambda (out)
    (write-json (combine-projects) out)))

; DEBUG
(print-hash-table #t)
(display (hash-ref (combine-projects) 'data))

