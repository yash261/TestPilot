Feature: Dashboard


  Scenario: Successful logout
    Given I am on the login page at http://localhost:3000/
    And I enter 'user' into the username field
    And I enter 'pass' into the password field
    And I click the 'Login' button
    And I am on the Dashboard page at http://localhost:3000/dashboard
    When I click the 'Logout' button
    Then I should be redirected to the landing page at http://localhost:3000/
