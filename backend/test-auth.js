const axios = require('axios');

const API_URL = 'http://localhost:4000/api';

// Test user credentials
const testUser = {
  username: 'testuser',
  email: 'test@example.com',
  password: 'testpassword123'
};

async function testAuth() {
  try {
    console.log('🚀 Starting authentication tests...\n');

    // 1. Test Signup
    console.log('1. Testing Signup...');
    const signupResponse = await axios.post(`${API_URL}/auth/signup`, testUser);
    console.log('✅ Signup successful!');
    console.log('Token received:', signupResponse.data.token);
    console.log('User data:', signupResponse.data.user);
    console.log('\n');

    // Store the token for subsequent requests
    const token = signupResponse.data.token;

    // 2. Test Login
    console.log('2. Testing Login...');
    const loginResponse = await axios.post(`${API_URL}/auth/login`, {
      email: testUser.email,
      password: testUser.password
    });
    console.log('✅ Login successful!');
    console.log('Token received:', loginResponse.data.token);
    console.log('\n');

    // 3. Test Protected Route (Create Chat)
    console.log('3. Testing Protected Route (Create Chat)...');
    const chatResponse = await axios.post(
      `${API_URL}/chat`,
      { websiteUrl: 'https://example.com' },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    console.log('✅ Chat creation successful!');
    console.log('Chat data:', chatResponse.data);
    console.log('\n');

    // 4. Test Invalid Token
    console.log('4. Testing Invalid Token...');
    try {
      await axios.post(
        `${API_URL}/chat`,
        { websiteUrl: 'https://example.com' },
        { headers: { Authorization: 'Bearer invalid_token' } }
      );
    } catch (error) {
      console.log('✅ Invalid token test passed! (Expected error)');
      console.log('Error message:', error.response?.data?.message);
    }
    console.log('\n');

    console.log('🎉 All tests completed successfully!');
  } catch (error) {
    console.error('❌ Test failed:', error.response?.data?.message || error.message);
  }
}

// Run the tests
testAuth(); 