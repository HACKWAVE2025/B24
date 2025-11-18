import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, ArrowRight } from 'lucide-react';
import { Separator } from '@/components/ui/separator';

const getScoreStyles = (score) => {
  if (score >= 70) {
    return {
      badge: 'bg-red-500/10 text-red-500 border border-red-500/40',
      shadow: 'shadow-red-200',
    };
  }
  if (score >= 40) {
    return {
      badge: 'bg-amber-500/10 text-amber-500 border border-amber-500/40',
      shadow: 'shadow-amber-200',
    };
  }
  return {
    badge: 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/40',
    shadow: 'shadow-emerald-200',
  };
};

const CLUSTER_COPY = {
  'loan scam': 'Loan Scam',
  'otp scam': 'OTP Scam',
  'fake job scam': 'Fake Job Scam',
  'investment scam': 'Investment Scam',
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'Unknown activity';
  try {
    return new Date(timestamp).toLocaleString();
  } catch (error) {
    return timestamp;
  }
};

const ThreatReceiverCard = ({
  receiver,
  score,
  patternFlags = [],
  cluster,
  lastSeen,
  onSelect,
  delay = 0,
}) => {
  const scoreStyles = getScoreStyles(score);
  const clusterLabel = CLUSTER_COPY[cluster?.toLowerCase?.()] || cluster || 'General Scam';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <Card className={`h-full border border-gray-200 dark:border-gray-800 hover:border-indigo-300 transition-all duration-200 ${scoreStyles.shadow}`}>
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-2">
            <div>
              <CardTitle className="text-lg font-semibold break-all">{receiver}</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">Last seen: {formatTimestamp(lastSeen)}</p>
            </div>
            <Badge className={`${scoreStyles.badge}`}>
              CTIH {Math.round(score)}%
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Activity className="w-4 h-4 text-indigo-500" />
            <span>{clusterLabel}</span>
          </div>
          <Separator />
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">Pattern Flags</p>
            <div className="flex flex-wrap gap-2">
              {patternFlags?.length
                ? patternFlags.slice(0, 4).map((flag) => (
                    <Badge key={flag} variant="secondary" className="text-xs">
                      {flag}
                    </Badge>
                  ))
                : <Badge variant="outline" className="text-xs">No recent flags</Badge>
              }
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button
            variant="ghost"
            className="ml-auto gap-2 text-indigo-600 dark:text-indigo-400"
            onClick={() => onSelect?.(receiver)}
          >
            View timeline
            <ArrowRight className="w-4 h-4" />
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  );
};

export default ThreatReceiverCard;

