(define (problem mission1)
  (:domain spaceDomain)

  (:objects
      ;waypoints
      w1 w2 w3 w4 w5 - waypoint
      ;images
      image1 image2 image3 image4 image5 - image
      ;scans
      scan1 scan2 scan3 scan4 scan5 - scan
      ;samples
      sample1 sample2 sample3 sample4 sample5 - sample
      ;rovers
      rover1 - rover
      ;landers
      lander1 - lander
  )

  (:init
      ;waypoint connections
      (traversable w1 w2)
      (traversable w1 w4)
      (traversable w2 w3)
      (traversable w3 w5)
      (traversable w4 w3)
      (traversable w5 w1)

      ;images at waypoints
      (imageAt image1 w1)
      (imageAt image2 w2)
      (imageAt image3 w3)
      (imageAt image4 w4)
      (imageAt image5 w5)

      ;scans at waypoints
      (scanAt scan1 w1)
      (scanAt scan2 w2)
      (scanAt scan3 w3)
      (scanAt scan4 w4)
      (scanAt scan5 w5)

      ;samples at waypoints
      (sampleAt sample1 w1)
      (sampleAt sample2 w2)
      (sampleAt sample3 w3)
      (sampleAt sample4 w4)
      (sampleAt sample5 w5)

      ;lander state
      (landerUndeployed lander1)
      (landerDoesNotHaveSample lander1)

      ;rover state
      (roverUndeployed rover1)
      (belongsTo rover1 lander1)
      (roverDoesNotHaveData rover1)
  )

  (:goal
      (and
          (dataCollected image5)
          (dataCollected scan3)
          (sampleCollected sample1)
      )
  )
)

