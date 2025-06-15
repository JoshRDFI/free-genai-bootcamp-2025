import React, { useState, useEffect } from 'react';
import { DndProvider, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Sentence, SentencePart as SentencePartType } from '../types/sentence';
import { SentencePart } from './SentencePart';
import { sentenceService } from '../services/sentenceService';

interface DropItem {
    id: string;
    index: number;
}

const SentenceDropZone: React.FC<{
    onDrop: (item: DropItem) => void;
    parts: SentencePartType[];
}> = ({ onDrop, parts }) => {
    const [{ isOver }, drop] = useDrop(() => ({
        accept: 'SENTENCE_PART',
        drop: (item: DropItem) => {
            onDrop(item);
            return undefined;
        },
        collect: (monitor) => ({
            isOver: monitor.isOver(),
        }),
    }));

    return (
        <div
            ref={drop}
            className={`
                min-h-[100px] p-4 rounded-lg border-2 border-dashed
                ${isOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
                flex flex-wrap items-center gap-2
            `}
        >
            {parts.map((part, index) => (
                <SentencePart 
                    key={`${part.id}-${index}`} 
                    part={part} 
                    index={index}
                    isDraggable={false}
                />
            ))}
        </div>
    );
};

export const SentenceConstructor: React.FC = () => {
    const [sentences, setSentences] = useState<Sentence[]>([]);
    const [currentSentence, setCurrentSentence] = useState<Sentence | null>(null);
    const [constructedParts, setConstructedParts] = useState<SentencePartType[]>([]);
    const [availableParts, setAvailableParts] = useState<SentencePartType[]>([]);
    const [feedback, setFeedback] = useState<string>('');
    const [startTime, setStartTime] = useState<number>(0);

    useEffect(() => {
        loadSentences();
    }, []);

    const loadSentences = async () => {
        try {
            const data = await sentenceService.getSentences();
            setSentences(data);
            if (data.length > 0) {
                setCurrentSentence(data[0]);
                setAvailableParts(data[0].sentence_parts.components);
                setStartTime(Date.now());
            }
        } catch (error) {
            console.error('Failed to load sentences:', error);
        }
    };

    const handleDrop = (item: DropItem) => {
        const part = availableParts.find((p) => p.id === item.id);
        if (part) {
            setConstructedParts(prev => [...prev, part]);
            setAvailableParts(prev => prev.filter((p) => p.id !== item.id));
        }
    };

    const checkAnswer = async () => {
        if (!currentSentence) return;

        const correctOrder = currentSentence.sentence_parts.correct_order;
        const constructedOrder = constructedParts.map(part => part.id);
        
        console.log('Correct order:', correctOrder);
        console.log('Constructed order:', constructedOrder);
        console.log('Are they equal?', JSON.stringify(constructedOrder) === JSON.stringify(correctOrder));
        
        const isCorrect = JSON.stringify(constructedOrder) === JSON.stringify(correctOrder);

        try {
            const timeTaken = (Date.now() - startTime) / 1000; // Convert to seconds
            await sentenceService.submitSentenceAttempt(
                currentSentence.id,
                constructedParts.map(part => part.text).join(''),
                timeTaken
            );

            setFeedback(
                isCorrect
                    ? 'Correct! Well done!'
                    : `Not quite right. Remember: 
                       1. Start with the subject 
                       2. Then the object 
                       3. End with the verb`
            );

            if (isCorrect) {
                setTimeout(() => {
                    const currentIndex = sentences.findIndex(
                        (s) => s.id === currentSentence.id
                    );
                    if (currentIndex < sentences.length - 1) {
                        const nextSentence = sentences[currentIndex + 1];
                        setCurrentSentence(nextSentence);
                        setAvailableParts(nextSentence.sentence_parts.components);
                        setConstructedParts([]);
                        setFeedback('');
                        setStartTime(Date.now());
                    }
                }, 2000);
            }
        } catch (error) {
            console.error('Failed to submit attempt:', error);
            setFeedback('An error occurred. Please try again.');
        }
    };

    const resetCurrentSentence = () => {
        if (currentSentence) {
            setAvailableParts(currentSentence.sentence_parts.components);
            setConstructedParts([]);
            setFeedback('');
            setStartTime(Date.now());
        }
    };

    if (!currentSentence) {
        return <div>Loading...</div>;
    }

    return (
        <DndProvider backend={HTML5Backend}>
            <div className="max-w-4xl mx-auto p-6">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold mb-4">Construct the Sentence</h2>
                    <div className="bg-blue-50 p-4 rounded-lg mb-4">
                        <p className="text-blue-800 font-medium mb-2">How to use:</p>
                        <ol className="list-decimal list-inside text-blue-700 space-y-1">
                            <li>Drag all three parts from the "Available Parts" section below</li>
                            <li>Drop them in the "Your Construction" box in the correct order</li>
                            <li>Click "Check Answer" to verify your sentence</li>
                            <li>Use "Reset" if you want to start over</li>
                        </ol>
                    </div>
                    <p className="text-gray-600 mb-2">
                        {currentSentence.source_language.text}
                    </p>
                    <p className="text-sm text-gray-500">
                        Grammar points: {currentSentence.target_language.grammar_points.join(', ')}
                    </p>
                </div>

                <div className="mb-8">
                    <h3 className="text-lg font-semibold mb-2">Available Parts</h3>
                    <div className="flex flex-wrap gap-2">
                        {availableParts.map((part, index) => (
                            <SentencePart 
                                key={part.id} 
                                part={part} 
                                index={index}
                                isDraggable={true}
                            />
                        ))}
                    </div>
                </div>

                <div className="mb-8">
                    <h3 className="text-lg font-semibold mb-2">Your Construction</h3>
                    <SentenceDropZone
                        onDrop={handleDrop}
                        parts={constructedParts}
                    />
                </div>

                {feedback && (
                    <div
                        className={`p-4 mb-4 rounded-lg ${
                            feedback.includes('Correct')
                                ? 'bg-green-100 text-green-700'
                                : 'bg-red-100 text-red-700'
                        }`}
                    >
                        {feedback}
                    </div>
                )}

                <div className="flex gap-4">
                    <button
                        onClick={checkAnswer}
                        className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={constructedParts.length === 0}
                    >
                        Check Answer
                    </button>
                    <button
                        onClick={resetCurrentSentence}
                        className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                    >
                        Reset
                    </button>
                </div>
            </div>
        </DndProvider>
    );
}; 