Feature: Signup Functionality


  Scenario: Unsuccessful signup with empty username
    Given I am on the signup page at http://localhost:3000/signup
    And I enter '' into the username field
    And I enter 'password' into the password field
    When I click the 'Sign Up' button
    Then I should see an error message indicating username already taken