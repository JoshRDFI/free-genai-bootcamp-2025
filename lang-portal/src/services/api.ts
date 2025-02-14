export async function getSessions(page: number, pageSize: number): Promise<Session[]> {
    const response = await fetch(`/api/sessions?page=${page}&size=${pageSize}`)
    if (!response.ok) throw new Error('Failed to fetch sessions')
    return response.json()
  }