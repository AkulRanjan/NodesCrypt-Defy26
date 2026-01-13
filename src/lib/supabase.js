import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://izfnuptqielzripwenii.supabase.co';
const supabaseAnonKey = 'sb_publishable_vrT4tYMUb-T5EkHC68EQ3A_vgdjPZCd';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
