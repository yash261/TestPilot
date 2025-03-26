Feature: Signup


  Scenario: Unsuccessful signup with missing username
    Given I am on the signup page at http://localhost:3000/signup
    And I enter "" into the username field
    And I enter "pass" into the password field
    When I click the "Sign Up" button
    Then I see an error message indicating the username is required
