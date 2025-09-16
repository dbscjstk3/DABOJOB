package com.dabojob;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController("/api/health")
public class HealthController {

	@GetMapping
	public String health() {
		return "OK";
	}
}


