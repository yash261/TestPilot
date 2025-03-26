Feature: Login Component


  Scenario: Successful login displays success message
    Given I am on the login page at http://localhost:3000/
    And I enter "user" in the username field
    And I enter "pass" in the password field
    When I click the 'Login' button
    Then A success message is displayed
