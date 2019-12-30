#lang racket
(require typed/racket
         (only-in gregor datetime)
         data/maybe)

(define spliter "«")
(struct Project
  ([project-name : String]           ;
   [outdoor-spot : String]           ; FK
   [location : String]               ; FK
   [construction_company : String]
   [tech_support_company : String]
   [project_company : String]
   [floor : Integer]
   [latitude : Flonum]
   [longitude : Flonum]
   [district : String]
   [area : Flonum]
   [demo_area : Flonum]
   [building_type : String]
   [building_height : Flonum]

   [started-time : Date]
   [finished-time : Date]
   [record-started_from : Date]
   [description : String]))

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
     [splited (letrec ([rec
                         (lambda (str keys)
                           (if (null? keys)
                             str
                             (rec (insert-line str (car keys)) (cdr keys))))])
                (rec str special-case-list))]
     [proj-info (list-ref (regexp-split "其他" splited) 0)])
    (match-let*
      ([(list a b) (split-to-cdr "示范工程技术亮点" proj-info)]
       [lista (map (curry regexp-split "\n") (docs-data->list a))]
       [listb (list (regexp-split spliter b))])
      (append lista listb))))

(define-type Parser (-> Parser (Listof String) (Maybe String)))

(: parse (-> Parser (Listof String) (Maybe String)))
(define (parse input parser)
  (let ([result (parser input)])
    (if (just? result)
      result
      nothing)))

#| ----------------------- |#
#| -  parser combinator  - |#
#| ----------------------- |#
(define (alt . parsers)
  (lambda (input)
    (let ([reslist (filter just? (map (curry parse input) parsers))])
      (if (null? reslist)
        nothing
        (first reslist)))))


(define (parse-projectname input)
  (if (member "示范工程名称" input)
    (just (list-ref input 3))
    (nothing)))

(define (parse-location input)
  (if (member "示范工程地址" input)
    (just (list-ref input 1))
    (nothing)))

(define (parse-construction_company input)
  (if (member "建设单位" input)
    (just (list-ref input 1))
    (nothing)))

(define (parse-tech_support_company input)
  (if (member "技术支撑单位" input)
    (just (list-ref input 1))
    (nothing)))

(define (parse-project_company input)
  (if (member "负责单位" input)
    (just (list-ref input 1))
    (nothing)))

(define (parse-floor input)
  (if (member "建筑楼层数" input)
    (just (list-ref input 1))
    (nothing)))

(define (parse-demo_area  input)
  (if (member "示范面积" input)
    (just (list-ref input 1))
    (nothing)))

(define (parse-area input)
  (if (member "建筑面积" input)
    (just (list-ref input 1))
    (nothing)))

(define (parse-building_type input)
  (if (member "示范工程类型" input)
    (just (list-ref input 1))
    (nothing)))

(define (parse-building_height input)
  (if (member "建筑高度" input)
    (just (list-ref input 1))
    (nothing)))


(: parse-datetime (-> String -> Datetime))
(define (parse-datetime datestring)
  (apply datetime (map string->number (regexp-split "\\." datestring))))

(define (parse-started-time input)
  (if (member "开工时间" input)
    (just (parse-datetime (list-ref input 1)))
    (nothing)))

(define (parse-finished-time input)
  (if (member "竣工时间" input)
    (just (parse-datetime (list-ref input 1)))
    (nothing)))

(define (parse-record-started_from input)
  (if (member "开始监测时间" input)
    (just (parse-datetime (list-ref input 1)))
    (nothing)))

(define (parse-description input)
  (if (member "示范工程技术亮点" input)
    (just (list-ref input 1))
    (nothing)))


(define parser (alt (list parse-projectname parse-location parse-construction_company)))


(define data
  (crop-proj-info
    (file->string "../../../doc/shisanwu_txt/a1.txt")))

(displayln (parser (list-ref data 1)))




