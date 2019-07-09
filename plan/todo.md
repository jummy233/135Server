- Platform
    - frontend
        - vuejs
            -template
                - Map template
                - devices template
                    - visualization modals
            - routes
                - Map <---------------------------------------------- api/projects GET
                    - Projects <------------------------------------- api/projects GET
                    - Projects/<Project id> <------------------------ api/projects/<project_id> GET
                    - Projects/<Project id>/Spots/<Spot id> <-------- api/spots/<spot_id> GET

                - RealtimeMap <--------------------------------------- api/
                    - RealTimeProjects/<Project id> <----------------- api/
                    - RealTimeProjects/<Project id>/Spots/<Spot id> <- api/

                - Comparison <---------------------------------------- api/
                    - Comparison/<Spot id>/<Spot id> <---------------- api/

                - Print <--------------------------------------------- api/
                    - Print/<Spot id> <------------------------------- api/

                - Error handling

    - backend [DOING]
        - flask backend
            - RESTful api
                - api/projects GET                              // get project list from Project table with location
                - api/project/<project_id> GET                  // get info of one specific project
                - api/spots/<spot_id> GET                       // get spot

            - RESTful api test [DONE]
            - flask config [DONE]
            - authorization functions
            - Realtime modules
        - sqlite3 database
            - table design [DONE]
            - database setup {DONE}
            - models test <DONE>
            - database api design [DONE]
            - database api test [DONE]

NOTE: Binary are converted into base64, base64 need to be converted into binary at frontend

2019-07-02
     made test framework
     made restful api for basic models
     made restful api for views

    tomorrow:
        finish restful api and tests.
        start vuejs.

NOTE: translate doc to Chinese.
NOTE: connect front end and back end.
NOTE: create backend api.

1. Frontend layout.                         (DONE)
    1. togglable side bar (bootstrap + css)
    2. top banner   ()

----------------- NOW -------------------------
1. The map page.
    1. a css china map
        1. leaflet js lib
        2. openmap map provider
        3. mappa.js map canvas

