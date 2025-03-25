package com.example.banking_app.controller;

import com.example.banking_app.model.Transaction;
import com.example.banking_app.model.User;
import com.example.banking_app.service.BankingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class BankingController {

    @Autowired
    private BankingService bankingService;

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody Map<String, String> credentials) {
        User user = bankingService.login(credentials.get("username"), credentials.get("password"));
        if (user == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "Invalid credentials"));
        }
        Map<String, Object> response = new HashMap<>();
        response.put("userId", user.getId());
        response.put("username", user.getUsername());
        response.put("balance", user.getBalance());
        return ResponseEntity.ok(response);
    }

    @PostMapping("/signup")
    public ResponseEntity<Map<String, Object>> signup(@RequestBody Map<String, String> credentials) {
        User user = bankingService.signup(credentials.get("username"), credentials.get("password"));
        if (user == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "Username already taken"));
        }
        Map<String, Object> response = new HashMap<>();
        response.put("userId", user.getId());
        response.put("username", user.getUsername());
        response.put("balance", user.getBalance());
        return ResponseEntity.ok(response);
    }

    @PostMapping("/transfer")
    public ResponseEntity<String> transfer(@RequestBody Map<String, Object> transferData) {
        String fromUserId = transferData.get("fromUserId").toString();
        String toUserId = transferData.get("toUserId").toString();
        double amount = Double.parseDouble(transferData.get("amount").toString());

        boolean success = bankingService.transfer(fromUserId, toUserId, amount);
        if (!success) {
            return ResponseEntity.badRequest().body("Transfer failed");
        }
        return ResponseEntity.ok("Transfer successful");
    }

    @GetMapping("/users")
    public ResponseEntity<List<User>> getUsers() {
        return ResponseEntity.ok(bankingService.getUsers());
    }

    @GetMapping("/transactions/{userId}")
    public ResponseEntity<List<Transaction>> getTransactions(@PathVariable String userId) {
        return ResponseEntity.ok(bankingService.getTransactions(userId));
    }
}