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

    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    if (!supabase) {
        return res.status(500).json({ error: 'Database connection failed' });
    }

    try {
        // Get start and end of today
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        // SQL equivalent:
        // SELECT w.username, SUM(w.reps) as total_reps, MIN(u.daily_goal) as daily_goal
        // FROM workout_log w
        // INNER JOIN users u ON w.username = u.username
        // WHERE w.created_at >= start_of_day AND w.created_at < end_of_day
        // GROUP BY w.username
        // ORDER BY total_reps DESC

        // Since Supabase JS client doesn't heavily support grouping with joined tables out-of-the-box easily without an RPC, 
        // we'll fetch today's logs and users, then aggregate in JS for this serverless function.
        // For a production app, an RPC function in Postgres is recommended.

        const { data: logs, error: logError } = await supabase
            .from('workout_log')
            .select(`
        username,
        reps,
        created_at,
        users ( daily_goal )
      `)
            .gte('created_at', today.toISOString())
            .lt('created_at', tomorrow.toISOString());

        if (logError) {
            console.error("Error fetching logs:", logError);
            return res.status(500).json({ error: 'Failed to fetch leaderboard logs' });
        }

        // Aggregate the data
        const aggregated = {};
        for (const log of logs) {
            if (!aggregated[log.username]) {
                aggregated[log.username] = {
                    username: log.username,
                    total_reps: 0,
                    daily_goal: log.users?.daily_goal || 100 // Fallback if join fail
                };
            }
            aggregated[log.username].total_reps += log.reps;
        }

        // Convert object to array and sort by total_reps DESC
        const leaderboard = Object.values(aggregated).sort((a, b) => b.total_reps - a.total_reps);

        return res.status(200).json({ data: leaderboard });

    } catch (err) {
        console.error("Unexpected error in get_leaderboard:", err);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
}
