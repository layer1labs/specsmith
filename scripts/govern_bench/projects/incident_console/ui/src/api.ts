export type Incident = {
  id: string;
  title: string;
};

export async function listIncidents(): Promise<Incident[]> {
  throw new Error("T28: API client not implemented");
}
