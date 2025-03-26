Feature: Login Component


  Scenario: Unsuccessful login with invalid password
    Given I am on the login page at http://localhost:3000/
    And I enter "user" in the username field
    And I enter "invalid_password" in the password field
    When I click the 'Login' button
    Then An error message is displayed