/**
 * Supabase client configuration for authentication and database operations
 */
import { createClient } from '@supabase/supabase-js';

// Supabase configuration with validation
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

// Debug logging for Supabase configuration
console.log('🔧 Supabase Configuration Debug:');
console.log('  - REACT_APP_SUPABASE_URL:', supabaseUrl || 'Not set');
console.log('  - REACT_APP_SUPABASE_ANON_KEY:', supabaseAnonKey ? '[HIDDEN]' : 'Not set');

// Create mock client for when Supabase is not configured
const mockSupabaseClient = {
  auth: {
    signUp: () => Promise.resolve({ data: null, error: { message: 'Supabase not configured. Please set environment variables.' } }),
    signInWithPassword: () => Promise.resolve({ data: null, error: { message: 'Supabase not configured. Please set environment variables.' } }),
    signOut: () => Promise.resolve({ error: null }),
    getSession: () => Promise.resolve({ data: { session: null }, error: null }),
    onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } })
  }
};

// Validate Supabase configuration and create appropriate client
let supabaseClient;

if (!supabaseUrl || !supabaseAnonKey ||
    supabaseUrl === 'https://your-project-id.supabase.co' ||
    supabaseAnonKey === 'your-supabase-anon-key') {
  console.error('❌ Supabase configuration missing or invalid!');
  console.error('Please set REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY in your .env file');
  supabaseClient = mockSupabaseClient;
} else {
  // Create real Supabase client
  supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true
    }
  });
  console.log('✅ Supabase client created successfully');
}

export const supabase = supabaseClient;
export default supabase;
