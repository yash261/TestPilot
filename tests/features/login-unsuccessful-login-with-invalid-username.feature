Feature: Login Component


  Scenario: Unsuccessful login with invalid username
    Given I am on the login page at http://localhost:3000/
    And I enter "invalid_user" in the username field
    And I enter "pass" in the password field
    When I click the 'Login' button
    Then An error message is displayed
