import { supabase } from './supabaseClient.js';

export default async function handler(req, res) {
    // CORS Headers
    res.setHeader('Access-Control-Allow-Credentials', true);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader(
        'Access-Control-Allow-Headers',
        'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
    );

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    if (!supabase) {
        return res.status(500).json({ error: 'Database connection failed' });
    }

    try {
        const { username, daily_goal } = req.body;

        if (!username || typeof daily_goal !== 'number' || daily_goal < 1) {
            return res.status(400).json({ error: 'Invalid payload. Expected { username: string, daily_goal: number (>0) }' });
        }

        // Upsert the user with the new goal
        const { data: userData, error: userError } = await supabase
            .from('users')
            .upsert({ username: username, daily_goal: daily_goal }, { onConflict: 'username' })
            .select();

        if (userError) {
            console.error("Error updating user goal:", userError);
            return res.status(500).json({ error: 'Failed to update goal' });
        }

        return res.status(200).json({ message: 'Goal updated successfully!', data: userData });

    } catch (err) {
        console.error("Unexpected error in update_goal:", err);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
}
