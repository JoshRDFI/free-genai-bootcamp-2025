import React from 'react';
import { useDrag } from 'react-dnd';
import { SentencePart as SentencePartType } from '../types/sentence';

interface Props {
    part: SentencePartType;
    index: number;
    isDraggable?: boolean;
}

export const SentencePart: React.FC<Props> = ({ part, index, isDraggable = true }) => {
    const [{ isDragging }, drag] = useDrag(() => ({
        type: 'SENTENCE_PART',
        item: { id: part.id, index },
        collect: (monitor) => ({
            isDragging: monitor.isDragging(),
        }),
        canDrag: isDraggable,
    }));

    return (
        <div
            ref={isDraggable ? drag : undefined}
            className={`
                px-4 py-2 m-1 rounded-lg
                ${isDraggable ? 'cursor-move' : ''}
                ${isDragging ? 'opacity-50' : 'opacity-100'}
                ${part.is_required ? 'bg-blue-100' : 'bg-gray-100'}
                ${isDraggable ? 'hover:bg-blue-200' : ''}
                transition-colors duration-200
            `}
            title={part.grammar_notes}
        >
            {part.text}
        </div>
    );
}; 