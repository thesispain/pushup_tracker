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
        const { username, reps } = req.body;

        if (!username || typeof reps !== 'number') {
            return res.status(400).json({ error: 'Invalid payload. Expected { username: string, reps: number }' });
        }

        // 1. Ensure user exists in 'users' table (Upsert)
        const { error: userError } = await supabase
            .from('users')
            .upsert({ username: username }, { onConflict: 'username', ignoreDuplicates: true });

        if (userError) {
            console.error("Error upserting user:", userError);
            return res.status(500).json({ error: 'Failed to find/create user' });
        }

        // 2. Insert the workout log
        const { data: logData, error: logError } = await supabase
            .from('workout_log')
            .insert([
                { username: username, reps: reps }
            ])
            .select();

        if (logError) {
            console.error("Error inserting log:", logError);
            return res.status(500).json({ error: 'Failed to save workout log' });
        }

        return res.status(200).json({ message: 'Workout saved successfully!', data: logData });

    } catch (err) {
        console.error("Unexpected error in save_workout:", err);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
}
