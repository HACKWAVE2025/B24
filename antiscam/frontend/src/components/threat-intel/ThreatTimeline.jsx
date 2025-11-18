import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts';
import { Loader2 } from 'lucide-react';

const formatHistory = (history = []) => {
  return history.map((entry) => {
    const riskScores = entry.agent_outputs?.map((agent) => Number(agent.risk_score) || 0) || [];
    const avgRisk = riskScores.length ? riskScores.reduce((acc, value) => acc + value, 0) / riskScores.length : 0;
    const flags = entry.agent_outputs?.flatMap((agent) => agent.evidence || []) || [];

    return {
      timestamp: entry.timestamp,
      label: entry.timestamp ? new Date(entry.timestamp).toLocaleString() : 'Recent event',
      threatScore: Number(avgRisk.toFixed(1)),
      flags,
      transaction: entry.transaction,
    };
  });
};

const ThreatTimeline = ({ receiver, history = [], loading, error }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  const formattedHistory = formatHistory(history);

  if (!formattedHistory.length) {
    return (
      <Card className="border border-dashed">
        <CardContent className="py-8 text-center text-muted-foreground">
          No threat events recorded yet for this receiver.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Threat Score Timeline</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={formattedHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="threatScore" stroke="#ec4899" strokeWidth={3} dot />
              {formattedHistory
                .filter((entry) => entry.threatScore >= 75)
                .map((entry) => (
                  <ReferenceDot
                    key={entry.timestamp}
                    x={entry.label}
                    y={entry.threatScore}
                    r={6}
                    fill="#ef4444"
                    stroke="none"
                  />
                ))}
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Agent Evidence Log</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-64">
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {formattedHistory.map((entry) => (
                <div key={entry.timestamp} className="p-4 space-y-3">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold">{entry.label}</p>
                      <p className="text-xs text-muted-foreground break-all">
                        ₹{entry.transaction?.amount?.toLocaleString?.() || '—'} • {entry.transaction?.reason || 'No reason shared'}
                      </p>
                    </div>
                    <Badge className={entry.threatScore >= 70 ? 'bg-red-500/10 text-red-600' : entry.threatScore >= 40 ? 'bg-amber-500/10 text-amber-600' : 'bg-emerald-500/10 text-emerald-600'}>
                      {entry.threatScore}%
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {entry.flags.length ? (
                      entry.flags.slice(0, 4).map((flag, index) => (
                        <Badge key={`${entry.timestamp}-${index}`} variant="outline" className="text-xs">
                          {flag}
                        </Badge>
                      ))
                    ) : (
                      <Badge variant="outline" className="text-xs text-muted-foreground">
                        No agent evidence captured
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default ThreatTimeline;

