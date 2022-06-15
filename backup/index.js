const hasValidHeader = (request, env) => {
    return request.headers.get('X-Custom-Auth-Key') === env.AUTH_KEY_SECRET;
};

export default {
    async fetch(request, env) {
        if (!hasValidHeader(request, env) || request.method !== 'POST') {
            return new Response('Forbidden', { status: 403 });
        }

        // generate timestamp
        const date = new Date()
        const iso = date.toISOString()
        const timestamp = iso.substring(0, iso.indexOf('T'));

        const key = `${timestamp}_db.sqlite3` // e.g. "2022-06-14_db.sqlite3"
        const file = await request.arrayBuffer()
        await env.BACKUPS.put(key, file);
        return new Response(`Put ${key} successfully!`);
    }
}
