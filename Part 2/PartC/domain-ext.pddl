
(define (domain lunar-extended)
    (:requirements
        :strips :typing
    )

    (:types
        ;all the types used in domain
        lander
        rover
        waypoint
        image
        scan
        sample
        astronaut
    )

    (:predicates
        (astronautAtControlRoom ?a - astronaut);location of astronaut
        (astronautAtDockingBay ?a - astronaut);location of astronaut
        (astronautLander ?a - astronaut ?l - lander) ;which lander the astronaut is in

        ;rover deployed?
        (roverUndeployed ?r - rover)
(roverDeployed ?r - rover)

        (roverAt ?r - rover ?w - waypoint) ;location of rover
        (roverDoesNotHaveData ?r - rover)
        (roverHasData ?r - rover)
        (roverData ?r - rover ?d - (either image scan)) ;data held by rover
        (collectedSample ?r - rover ?s - sample) ;sample collected by rover
        (belongsTo ?r - rover ?l - lander) ;which lander the rover belongs to
        
        ;lander deployed?
        (landerUndeployed ?l - lander)
        (landerDeployed ?l - lander)

        (landerAt ?l - lander ?w - waypoint) ;location of lander
        (landerData ?l - lander ?d - (either image scan)) ;data held by lander
        (landerDoesNotHaveSample ?l - lander)
        (landerHasSample ?l - lander)
        (landerSample ?l - lander ?s - sample) ;sample held by lander
        
        (imageAt ?i - image ?w - waypoint) ;Where does the image belong to
        (scanAt ?s - scan ?w - waypoint) ;Where does the scan belong to
        (sampleAt ?s - sample ?w - waypoint) ;Where does the sample belong to

        (traversable ?w1 - waypoint ?w2 - waypoint) ;are two waypoints connected

        ;goal predicates
        (dataCollected ?d - (either image scan)) ;data has been collected
        (sampleCollected ?s - sample) ;sample has been collected
    )

    ;moves the astronaut from docking bay to control room
    (:action moveAstronautControlRoom
        :parameters (?a - astronaut)
        :precondition 
            (and 
                (astronautAtDockingBay ?a)
            )
        :effect 
            (and 
                (not (astronautAtDockingBay ?a))
                (astronautAtControlRoom ?a)
            )
    )
    
    ;moves the astronaut from control room to docking bay
    (:action moveAstronautDockingBay
        :parameters (?a - astronaut)
        :precondition 
            (and 
                (astronautAtControlRoom ?a)
            )
        :effect 
            (and 
                (not (astronautAtControlRoom ?a))
                (astronautAtDockingBay ?a)
            )
    )
    
    ;moves the rover from one waypoint to another if its traversable
    (:action moveRover
        :parameters
            (?r - rover ?from - waypoint ?to - waypoint)
        :precondition
            (and
                (roverDeployed ?r)
                (roverAt ?r ?from)
                (traversable ?from ?to)
            )
        :effect
            (and
                (not (roverAt ?r ?from))
                (roverAt ?r ?to)
            )
    )

    ;takes scan if rover is at waypoint, rover is deployed, scan belongs to waypoint, and rover does not already have data
    (:action takeScan
        :parameters (?r - rover ?w - waypoint ?s - scan)
        :precondition 
            (and 
                (roverAt ?r ?w)
                (roverDeployed ?r)
                (scanAt ?s ?w)
                (roverDoesNotHaveData ?r)
            )
        :effect 
            (and 
                (not (roverDoesNotHaveData ?r))
                (roverData ?r ?s)
                (roverHasData ?r)
            )
    )

    ;only collects sample if rover is at waypoint, rover is deployed, and sample belongs to waypoint
    (:action collectSample
        :parameters (?r - rover ?w - waypoint ?s - sample)
        :precondition 
            (and 
                (roverAt ?r ?w)
                (roverDeployed ?r)
                (sampleAt ?s ?w)
            )
        :effect 
            (and 
                (collectedSample ?r ?s)
            )
    )

    ;only takes picture if rover is at waypoint, rover is deployed, image belongs to waypoint, and rover does not already have data
    (:action takePicture
        :parameters (?r - rover ?w - waypoint ?i - image)
        :precondition 
            (and 
                (roverDeployed ?r)
                (roverAt ?r ?w)
                (imageAt ?i ?w)
                (roverDoesNotHaveData ?r)
            )
        :effect 
            (and
                (not (roverDoesNotHaveData ?r))
                (roverData ?r ?i)
                (roverHasData ?r)
            )
    )

    ;only transmits data if rover has data and lander is deployed and belongs to the rover
    (:action transmitData
        :parameters (
            ?r - rover ?l - lander ?d - (either image scan) ?a - astronaut
        )
        :precondition 
            (and 
                (roverDeployed ?r)
                (roverHasData ?r)
                (roverData ?r ?d)
                (landerDeployed ?l)
                (belongsTo ?r ?l)
                (astronautLander ?a ?l)
                (astronautAtControlRoom ?a)
            )
        :effect 
            (and 
                (roverDoesNotHaveData ?r)
                (not (roverData ?r ?d) )
                (not (roverHasData ?r))
                (landerData ?l ?d)
                (dataCollected ?d)
            )
    )

    ;deposits sample from rover to lander if rover is at lander's waypoint, rover is deployed, rover belongs to lander, rover has collected sample, and lander does not already have a sample
    (:action depositSample
        :parameters (?r - rover ?l - lander ?s - sample ?w - waypoint ?a - astronaut)
        :precondition 
            (and 
                (landerAt ?l ?w)
                (belongsTo ?r ?l)
                (roverDeployed ?r)
                (collectedSample ?r ?s)
                (roverAt ?r ?w)
                (landerDoesNotHaveSample ?l)
                (astronautLander ?a ?l)
                (astronautAtDockingBay ?a)
            )
        :effect 
            (and 
                (not (landerDoesNotHaveSample ?l))
                (not (collectedSample ?r ?s))
                (landerHasSample ?l)
                (landerSample ?l ?s)
                (sampleCollected ?s)
            )
    )

    ;deploys rover from lander if rover is undeployed, belongs to lander, lander is deployed, and lander is at waypoint
    (:action deployRover
        :parameters 
            (?r - rover ?l - lander ?w - waypoint ?a - astronaut)
        :precondition 
            (and 
                (roverUndeployed ?r)
                (belongsTo ?r ?l)
                (landerDeployed ?l)
                (landerAt ?l ?w)
                (astronautLander ?a ?l)
                (astronautAtDockingBay ?a)
            )
        :effect 
            (and 
                (not (roverUndeployed ?r))
                (roverDeployed ?r)
                (roverAt ?r ?w)
            )
    )

    ;deploys lander at waypoint if lander is undeployed
    (:action deployLander
        :parameters 
            (?l - lander ?w - waypoint)
        :precondition 
            (and 
                (landerUndeployed ?l)
            )
        :effect 
            (and 
                (not (landerUndeployed ?l))
                (landerDeployed ?l)
                (landerAt ?l ?w)
            )
    )

)