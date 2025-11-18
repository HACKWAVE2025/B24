import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

const ClusterCard = ({ cluster = {}, delay = 0 }) => {
  const {
    name,
    averageScore,
    avgScore,
    count,
    size,
    members = [],
    topKeywords = [],
    updatedAt,
    isEmerging = false,
    active = true,
  } = cluster;

  const resolvedScore = typeof averageScore === 'number'
    ? averageScore
    : typeof avgScore === 'number'
      ? avgScore
      : 0;

  const resolvedCount = typeof count === 'number'
    ? count
    : typeof size === 'number'
      ? size
      : members.length;

  const updatedLabel = updatedAt ? new Date(updatedAt).toLocaleString() : 'Awaiting signals';
  const statusLabel = isEmerging ? 'Emerging' : active ? 'Active' : 'Inactive';
  const statusVariant = isEmerging ? 'destructive' : active ? 'secondary' : 'outline';
  const keywordTokens = Array.isArray(topKeywords) ? topKeywords.slice(0, 4) : [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <Card
        className={[
          'h-full border transition-all duration-200 hover:border-indigo-300',
          isEmerging ? 'border-amber-400 ring-2 ring-amber-100/60 dark:ring-amber-400/40' : 'border-gray-200 dark:border-gray-800',
          active ? 'bg-white dark:bg-slate-900' : 'bg-muted/30',
        ].join(' ')}
      >
        <CardHeader>
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <CardTitle className="text-xl flex items-center gap-2">{name}</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-sm">
                {resolvedCount} receivers
              </Badge>
              <Badge variant={statusVariant} className="text-xs uppercase">
                {statusLabel}
              </Badge>
            </div>
          </div>
          <CardDescription>Updated {updatedLabel}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground">Average Threat Score</p>
            <p
              className={`text-3xl font-bold ${
                resolvedScore >= 70 ? 'text-red-500' : resolvedScore >= 40 ? 'text-amber-500' : 'text-emerald-500'
              }`}
            >
              {Number(resolvedScore || 0).toFixed(1)}%
            </p>
          </div>
          <Separator />
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Top Keywords</p>
            {keywordTokens.length ? (
              <div className="flex flex-wrap gap-2">
                {keywordTokens.map((keyword) => (
                  <Badge key={keyword} variant="outline" className="text-xs capitalize">
                    {keyword}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground italic">Signals still forming</p>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ClusterCard;

