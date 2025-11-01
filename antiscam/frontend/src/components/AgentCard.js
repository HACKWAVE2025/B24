import { useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from './ui/collapsible';

const AgentCard = ({ agent, darkMode }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="glass rounded-xl overflow-hidden" data-testid={`agent-card-${agent.name}`}>
        <CollapsibleTrigger className="w-full">
          <div className={darkMode ? "flex items-center justify-between p-4 hover:bg-gray-700 cursor-pointer" : "flex items-center justify-between p-4 hover:bg-gray-50 cursor-pointer"}>
            <div className="flex items-center gap-4">
              <div
                className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                style={{ backgroundColor: `${agent.color}20` }}
              >
                {agent.icon}
              </div>
              <div className="text-left">
                <h4 className={darkMode ? "font-semibold text-white" : "font-semibold text-gray-900"}>{agent.name}</h4>
                <p className={darkMode ? "text-sm text-gray-400" : "text-sm text-gray-600"}>{agent.message}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span
                className="px-3 py-1 rounded-full text-sm font-semibold"
                style={{ backgroundColor: `${agent.color}20`, color: agent.color }}
                data-testid={`risk-score-${agent.name}`}
              >
                {agent.riskScore}%
              </span>
              {isOpen ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
            </div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className={darkMode ? "px-4 pb-4 border-t border-gray-700" : "px-4 pb-4 border-t border-gray-200"}
          >
            <div className={darkMode ? "bg-gray-700 p-4 rounded-lg mt-4" : "bg-gray-50 p-4 rounded-lg mt-4"}>
              <p className={darkMode ? "text-sm text-gray-300 leading-relaxed" : "text-sm text-gray-700 leading-relaxed"}>{agent.details}</p>
              {agent.evidence && agent.evidence.length > 0 && (
                <div className="mt-3 space-y-1">
                  {agent.evidence.map((item, idx) => (
                    <div key={idx} className={darkMode ? "flex items-start gap-2 text-xs text-gray-400" : "flex items-start gap-2 text-xs text-gray-600"}>
                      <div className="w-1.5 h-1.5 rounded-full mt-1.5" style={{ backgroundColor: agent.color }}></div>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
};

export default AgentCard;
