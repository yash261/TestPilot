Feature: Signup


  Scenario: Unsuccessful signup with missing password
    Given I am on the signup page at http://localhost:3000/signup
    And I enter "user" into the username field
    And I enter "" into the password field
    When I click the "Sign Up" button
    Then I see an error message indicating the password is required