#!/bin/bash

echo "========================================="
echo "Microservices Health Check"
echo "========================================="
echo ""

echo "1. Checking Container Status..."
docker-compose -f docker-compose.microservices.yml ps
echo ""

echo "2. Checking Redis..."
docker-compose -f docker-compose.microservices.yml exec -T redis redis-cli ping 2>/dev/null && echo "✓ Redis is healthy" || echo "✗ Redis is down"
echo ""

echo "3. Checking API Gateway..."
curl -s http://localhost:5000/health 2>/dev/null && echo "✓ API Gateway is healthy" || echo "✗ API Gateway is down"
echo ""

echo "4. Checking Import Service..."
curl -s http://localhost:5001/health 2>/dev/null && echo "✓ Import Service is healthy" || echo "✗ Import Service is down"
echo ""

echo "5. Checking Metadata Service..."
curl -s http://localhost:5002/health 2>/dev/null && echo "✓ Metadata Service is healthy" || echo "✗ Metadata Service is down"
echo ""

echo "6. Checking Storage Service..."
curl -s http://localhost:5003/health 2>/dev/null && echo "✓ Storage Service is healthy" || echo "✗ Storage Service is down"
echo ""

echo "7. Checking Frontend..."
curl -s http://localhost:3000 > /dev/null 2>&1 && echo "✓ Frontend is accessible" || echo "✗ Frontend is down"
echo ""

echo "========================================="
echo "Recent Logs (Last 20 lines per service)"
echo "========================================="

echo ""
echo "=== Metadata Service Logs ==="
docker-compose -f docker-compose.microservices.yml logs --tail=20 metadata-service

echo ""
echo "=== Worker Service Logs ==="
docker-compose -f docker-compose.microservices.yml logs --tail=20 worker-service

echo ""
echo "========================================="
echo "Health check complete!"
echo "========================================="
