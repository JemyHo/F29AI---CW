(define (problem mission2)
  (:domain spaceDomain)

  (:objects
      ;waypoints
      w1 w2 w3 w4 w5 w6 - waypoint
      ;images
      image1 image2 image3 image4 image5 image6 - image
      ;scans
      scan1 scan2 scan3 scan4 scan5 scan6 - scan
      ;samples
      sample1 sample2 sample3 sample4 sample5 sample6 - sample
      ;rovers
      rover1 rover2 - rover
      ;landers
      lander1 lander2 - lander
  )

  (:init
      ;waypoint connections
      (traversable w1 w2)
      (traversable w2 w1)
      (traversable w2 w3)
      (traversable w2 w4)
      (traversable w3 w5)
      (traversable w4 w2)
      (traversable w5 w3)
      (traversable w5 w6)
      (traversable w6 w4)

      ;images at waypoints
      (imageAt image1 w1)
      (imageAt image2 w2)
      (imageAt image3 w3)
      (imageAt image4 w4)
      (imageAt image5 w5)
      (imageAt image6 w6)

      ;scans at waypoints
      (scanAt scan1 w1)
      (scanAt scan2 w2)
      (scanAt scan3 w3)
      (scanAt scan4 w4)
      (scanAt scan5 w5)
      (scanAt scan6 w6)

      ;samples at waypoints
      (sampleAt sample1 w1)
      (sampleAt sample2 w2)
      (sampleAt sample3 w3)
      (sampleAt sample4 w4)
      (sampleAt sample5 w5)
      (sampleAt sample6 w6)

      ;lander state
      (landerDeployed lander1)
      (landerDoesNotHaveSample lander1)
      (landerAt lander1 w2)

      (landerUndeployed lander2)
      (landerDoesNotHaveSample lander2)

      ;rover state
      (roverAt rover1 w2)
      (roverDeployed rover1)
      (belongsTo rover1 lander1)
      (roverDoesNotHaveData rover1)

      (roverUndeployed rover2)
      (belongsTo rover2 lander2)
      (roverDoesNotHaveData rover2)
  )

  (:goal
      (and
          (dataCollected image3)
          (dataCollected scan4)
          (dataCollected image2)
          (dataCollected scan6)
          (sampleCollected sample5)
          (sampleCollected sample1)
      )
  )
)

